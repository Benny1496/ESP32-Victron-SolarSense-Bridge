//! Test 30 (external harness): real model-command-to-drawing inspect probes for W23a.
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

// Compare actual CAD geometry against the original analytic W23a oracle volumes.
fn assert_analytic_volume(s: &mut Session, reference: f64, oracle: &str) {
    let reply = run(s, "inspect.measure", json!({}));
    assert_eq!(reply["body_count"], json!(1), "{oracle} unexpected bodies: {reply}");
    let value = reply["total"]["volume_mm3"].as_f64()
        .unwrap_or_else(|| panic!("{oracle} missing CAD volume: {reply}"));
    assert!((value-reference).abs() < reference.abs() * 0.001,
           "{oracle} CAD volume {value} differs from analytic {reference}");
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
        let changed = run(&mut self.session, "parameters.change",
                          json!({"name": "bore1_d", "expression": "12 mm"}));
        assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()), "{changed}");
        assert_analytic_volume(&mut self.session, 156167.25696262045, "oracle 86");
        self.open();
    }
}
fn plate_two_bores() -> Plate {
    let mut s = Session::default();
    // Replay the *real* official Oracle #84 sketch/extrude/solid.hole recipe.
    // The commands JSON comes from the actual pinned SolidCraft CLI recipe converter.
    let source = std::fs::read_to_string("ci-reports/w23a-test30/oracle84-commands.json")
        .expect("generated real Oracle84 command list");
    let script: Value = serde_json::from_str(&source).expect("oracle84 JSON");
    let steps = script["commands"].as_array().expect("commands");
    assert!(steps.len() > 3, "the real oracle must have several commands");
    let hole_count = steps.iter().filter(|step| step["command"] == "solid.hole").count();
    let extrusions = steps.iter().filter(|step| step["command"] == "solid.extrude").count();
    assert_eq!(hole_count, 2, "two real hole features expected");
    assert!(extrusions >= 1, "true extruded sketch required");
    for (index, step) in steps.iter().enumerate() {
        let cmd = step["command"].as_str().expect("command name");
        let params = step.get("params").cloned().unwrap_or_else(|| json!({}));
        let answer = s.execute(cmd, &params)
            .unwrap_or_else(|e| panic!("oracle84 command #{index}: {cmd} {params}: {e}"));
        if let Some(error) = answer.get("error") { panic!("oracle84 command #{index} ({cmd}) error: {error}"); }
    }
    assert_analytic_volume(&mut s, 156858.4073464102, "oracle 84 baseline");

    // Actually make a drawing and save a real top-view record through existing W19 API.
    run(&mut s, "drawing.create", json!({"name":"W23a test30"}));
    let mut d = (**s.drawing("test30").expect("open drawing")).clone();
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
fn w23a_t30_bore1_10_to_12_keeps_dimension_id_and_independent_bore2() {
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
fn w23a_t30_deleted_bore1_is_lost_never_bore2_then_undo() {
    let mut f = plate_two_bores();
    let id = f.bore1.clone();
    f.close();
    run(&mut f.session, "timeline.delete", json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session, 158429.2036732051, "oracle 87 after delete");
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

#[test]
fn w23a_t30_original_oracle84_change_undo_redo_preserves_measure_identity() {
    let mut f = plate_two_bores();
    let id = f.bore1.clone();
    f.change_bore1_to_12();
    assert_ok(&inspect(&mut f.session, &id), 12.0);
    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    assert_analytic_volume(&mut f.session, 156858.4073464102, "oracle 84 undo");
    f.open();
    assert_ok(&inspect(&mut f.session, &id), 10.0);
    assert_ok(&inspect(&mut f.session, &f.bore2), 10.0);
    f.close();
    run(&mut f.session, "edit.redo", json!({}));
    assert_analytic_volume(&mut f.session, 156167.25696262045, "oracle 86 redo");
    f.open();
    let final_dimension = inspect(&mut f.session, &id);
    assert_eq!(final_dimension["dimension"], id);
    assert_ok(&final_dimension, 12.0);
    assert_ok(&inspect(&mut f.session, &f.bore2), 10.0);
    println!("PASS: real W23a oracle84 sketch/hole dimension identity through parameter change, undo, redo");
}
