//! Test 28 (external harness): real model-command-to-drawing inspect probes for W23a.
 //! Changes only a disposable checkout. Not official W23a full view-update E2E.
use std::sync::Arc;
use serde_json::{json, Value};
use solidcraft_doc::drawing::view::{View, ViewKind, ViewPlace};
use solidcraft_doc::drawing_view::{ViewDirection, ViewOverrides};
use solidcraft_doc::ids::{self, IdSource};
use solidcraft_geom::drawing_view::NamedView;
use solidcraft_geom::Vec3;
use crate::Session;

fn run(s: &mut Session, command: &str, params: Value) -> Value {
    s.execute(command, &params).unwrap_or_else(|e| panic!("{command} {params}: {e}"))
}

fn index_of_bore_edge(s: &Session, centre: [f64; 3], radius: f64) -> usize {
    let c = Vec3::from(centre);
    let state = s.model.state();
    let mesh = state.body("Plate").expect("Plate body").mesh();
    mesh.edges.iter().position(|line| {
        line.len() >= 2 && line.iter().all(|p| (p.dist(c) - radius).abs() < 1e-5)
    }).unwrap_or_else(|| panic!("missing circular edge at {centre:?}, radius {radius}"))
}

fn inspect(s: &mut Session, id: &Value) -> Value {
    run(s, "drawing.dimension.inspect", json!({"dimension": id}))
}

fn assert_ok(reply: &Value, diameter_mm: f64) {
    assert_eq!(reply["status"], json!("ok"), "unexpected dimension state: {reply}");
    let v = reply["value"].as_f64().expect("measured dimension value");
    assert!((v - diameter_mm).abs() < 1e-8, "expected diameter {diameter_mm}, got {reply}");
    assert_eq!(reply["record"]["kind"]["radial"]["diameter"], json!(true), "{reply}");
}

struct Plate {
    session: Session,
    drawing: String,
    bore1: Value,
    bore2: Value,
}
impl Plate {
    fn open(&mut self) {
        run(&mut self.session, "drawing.open", json!({"drawing": self.drawing}));
    }
    fn close(&mut self) {
        run(&mut self.session, "drawing.close", json!({}));
    }
    fn change_bore1_to_12(&mut self) {
        self.close();
        let rows = run(&mut self.session, "parameters.list", json!({"filter":"feature"}));
        let p = rows["parameters"].as_array().expect("feature param list")
            .iter().find(|p| p["feature"] == "Bore1" &&
                     (p["input"] == "radius" || p["input"] == "diameter"))
            .unwrap_or_else(|| panic!("Bore1 radius/diameter input not found: {rows}"));
        let name = p["name"].as_str().expect("parameter name").to_string();
        let newval = if p["input"] == "radius" { "6 mm" } else { "12 mm" };
        let changed = run(&mut self.session, "parameters.change",
                          json!({"name": name, "expression": newval}));
        assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()), "{changed}");
        self.open();
    }
}
fn plate_two_bores() -> Plate {
    let mut s = Session::default();
    run(&mut s, "solid.box", json!({"length":100,"width":80,"height":20,
        "body_name":"Plate"}));
    run(&mut s, "solid.cylinder", json!({"radius":5,"height":22,
        "base":[20,20,-1],"axis":"Z","operation":"cut",
        "targets":["Plate"],"name":"Bore1"}));
    run(&mut s, "solid.cylinder", json!({"radius":5,"height":22,
        "base":[60,50,-1],"axis":"Z","operation":"cut",
        "targets":["Plate"],"name":"Bore2"}));

    // Actually make a drawing and save a real top-view record through existing W19 API.
    run(&mut s, "drawing.create", json!({"name":"W23a test28"}));
    let mut d = (**s.drawing("test28").expect("open drawing")).clone();
    let drawing = ids::encode(d.id);
    let view = d.allocate_id(&mut IdSource::seeded(28280)).expect("view ID");
    let (sheet, source) = (d.sheets[0].id, d.sources[0].id);
    d.add_views([Arc::new(View {
        id:view, sheet,
        kind: ViewKind::Base { source, view: ViewDirection::Named(NamedView::Top) },
        place: ViewPlace::At([205.0, 150.0]),
        settings: ViewOverrides { scale: Some("1:1".parse().unwrap()), ..ViewOverrides::default() },
        reference_margin_mm:0.0,
    })]);
    d.validate().expect("valid drawing and top view");
    s.doc_mut().put_drawing(Arc::new(d));

    // Both dimensions are added by the actual public W19d/W20a drawing commands.
    let one = index_of_bore_edge(&s, [20.0, 20.0, 20.0], 5.0);
    let two = index_of_bore_edge(&s, [60.0, 50.0, 20.0], 5.0);
    assert_ne!(one, two, "two distinct holes");
    let bore1 = run(&mut s, "drawing.dimension.add",
        json!({"view": ids::encode(view), "kind": {"radial": {
              "edge": {"body":"Plate","index":one}, "diameter":true}}}))["dimension"].clone();
    let bore2 = run(&mut s, "drawing.dimension.add",
        json!({"view": ids::encode(view), "kind": {"radial": {
              "edge": {"body":"Plate","index":two}, "diameter":true}}}))["dimension"].clone();
    assert_ne!(bore1, bore2);
    assert_ok(&inspect(&mut s, &bore1), 10.0);
    assert_ok(&inspect(&mut s, &bore2), 10.0);
    Plate {session:s, drawing, bore1, bore2}
}

#[test]
fn w23a_t28_bore1_10_to_12_keeps_dimension_id_and_independent_bore2() {
    let mut f = plate_two_bores();
    let id = f.bore1.clone();
    f.change_bore1_to_12();
    let a = inspect(&mut f.session, &f.bore1);
    assert_eq!(a["dimension"], id, "dimension ID changed");
    assert_ok(&a, 12.0);
    let other = inspect(&mut f.session, &f.bore2);
    assert_ok(&other, 10.0);
    println!("PASS: W23a E2E-01 early W19d/W20a inspect subset; diameter id={} now 12mm; Bore2 still 10mm",id);
}

#[test]
fn w23a_t28_deleted_bore1_is_lost_never_bore2_then_undo() {
    let mut f = plate_two_bores();
    let id = f.bore1.clone();
    f.close();
    run(&mut f.session, "timeline.delete", json!({"feature":"Bore1"}));
    f.open();
    let lost = inspect(&mut f.session, &f.bore1);
    assert_eq!(lost["dimension"], id, "dimension ID changed");
    assert_eq!(lost["status"], json!("lost"), "deleted Bore1 must be lost: {lost}");
    assert!(lost.get("value").is_none(), "lost Bore1 unexpectedly measures {lost}");
    let other = inspect(&mut f.session, &f.bore2);
    assert_ok(&other, 10.0);
    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    f.open();
    let restored = inspect(&mut f.session, &f.bore1);
    assert_eq!(restored["dimension"], id);
    assert_ok(&restored, 10.0);
    println!("PASS: W23a E2E-02 early W19d/W20a inspect subset; Bore1 lost, Bore2 unchanged, undo restores");
}
