//! Test 34 (external harness): real model-command-to-drawing inspect probes for W23a.
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
    let source = std::fs::read_to_string(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../ci-reports/w23a-test34/oracle84-commands.json"))
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
    run(&mut s, "drawing.create", json!({"name":"W23a test34"}));
    let mut d = (**s.drawing("test34").expect("open drawing")).clone();
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
fn w23a_t34_bore1_10_to_12_keeps_dimension_id_and_independent_bore2() {
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
fn w23a_t34_deleted_bore1_is_lost_never_bore2_then_undo() {
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
fn w23a_t34_original_oracle84_change_undo_redo_preserves_measure_identity() {
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

fn set_authored_text_at_paper(
    s: &mut Session, dimension: &Value, paper: [f64;2], view_centre: [f64;2]
) -> [f64;2] {
    // W19d text.at is relative to the centre of its view, NOT paper coordinates.
    let relative = [paper[0] - view_centre[0], paper[1] - view_centre[1]];
    let answer = run(s, "drawing.dimension.edit", json!({
        "dimension": dimension,
        "set": {"text": {"at": relative}}
    }));
    assert!(answer["changed"].as_array().is_some_and(|changes|
        changes.iter().any(|field| field == "text")), "text edit not applied: {answer}");
    relative
}

fn assert_text_relative(s: &mut Session, dimension: &Value, relative: [f64;2]) {
    let reply = inspect(s, dimension);
    assert_eq!(reply["dimension"], *dimension, "dimension id changed: {reply}");
    let at = reply["record"]["text"]["at"].as_array().unwrap_or_else(||
        panic!("text position missing from authored dimension: {reply}"));
    assert_eq!(at.len(), 2);
    for (i, goal) in relative.iter().enumerate() {
        let actual = at[i].as_f64().expect("numeric text position");
        assert!((actual-goal).abs()<1e-9, "text offset changed {relative:?}: {reply}");
    }
}

#[test]
fn w23a_t34_oracle85_width_80_to_100_preserves_two_hole_dimensions_and_undo_redo() {
    let mut f = plate_two_bores();
    let first = f.bore1.clone();
    let second = f.bore2.clone();
    f.close();
    let changed = run(&mut f.session, "parameters.change",
        json!({"name":"width", "expression":"100 mm"}));
    assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()), "{changed}");
    assert_analytic_volume(&mut f.session, 196858.4073464102, "oracle 85 width=100");
    f.open();
    let a=inspect(&mut f.session,&first); let b=inspect(&mut f.session,&second);
    assert_eq!(a["dimension"],first); assert_eq!(b["dimension"],second);
    assert_ok(&a,10.0); assert_ok(&b,10.0);
    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    assert_analytic_volume(&mut f.session,156858.4073464102,"oracle 84 width undo");
    f.open();
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    f.close();
    run(&mut f.session, "edit.redo", json!({}));
    assert_analytic_volume(&mut f.session,196858.4073464102,"oracle 85 width redo");
    f.open();
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    println!("PASS: original oracle85 width 80->100 and undo/redo leaves both measured hole IDs valid");
}

#[test]
fn w23a_t34_user_authored_sheet_text_positions_survive_diameter_edit_and_undo_redo() {
    let mut f = plate_two_bores();
    let first=f.bore1.clone();
    let second=f.bore2.clone();
    // View place in fixture is [205,150] millimetres on paper.
    let view_centre=[205.0,150.0];
    let first_relative=set_authored_text_at_paper(&mut f.session,&first,[95.0,55.0],view_centre);
    let second_relative=set_authored_text_at_paper(&mut f.session,&second,[145.0,55.0],view_centre);
    assert_eq!(first_relative,[-110.0,-95.0]);
    assert_eq!(second_relative,[-60.0,-95.0]);
    assert_text_relative(&mut f.session,&first,first_relative);
    assert_text_relative(&mut f.session,&second,second_relative);
    f.change_bore1_to_12();
    assert_ok(&inspect(&mut f.session,&first),12.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    assert_text_relative(&mut f.session,&first,first_relative);
    assert_text_relative(&mut f.session,&second,second_relative);
    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_text_relative(&mut f.session,&first,first_relative);
    assert_text_relative(&mut f.session,&second,second_relative);
    f.close();
    run(&mut f.session,"edit.redo",json!({}));
    f.open();
    assert_ok(&inspect(&mut f.session,&first),12.0);
    assert_text_relative(&mut f.session,&first,first_relative);
    assert_text_relative(&mut f.session,&second,second_relative);
    println!("PASS: authored dimension text.at stays at the same sheet position after model edit/undo/redo (record contract, not visual rendering)");
}

#[test]
fn w23a_t34_deleted_bore1_lost_then_undo_then_redo_preserves_authored_text_and_other_hole() {
    let mut f=plate_two_bores();
    let first=f.bore1.clone(); let second=f.bore2.clone();
    let at=set_authored_text_at_paper(&mut f.session,&first,[95.0,55.0],[205.0,150.0]);
    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session,158429.2036732051,"oracle 87 after Bore1 deletion");
    f.open();
    assert_eq!(inspect(&mut f.session,&first)["status"],json!("lost"));
    assert_text_relative(&mut f.session,&first,at);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_text_relative(&mut f.session,&first,at);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    f.close();
    run(&mut f.session,"edit.redo",json!({}));
    assert_analytic_volume(&mut f.session,158429.2036732051,"oracle 87 deletion redone");
    f.open();
    let lost=inspect(&mut f.session,&first);
    assert_eq!(lost["dimension"],first);
    assert_eq!(lost["status"],json!("lost"));
    assert!(lost.get("value").is_none());
    assert_text_relative(&mut f.session,&first,at);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    println!("PASS: Bore1 lost/undo/redo keeps authored text and never silently becomes Bore2");
}

// W13/W14's existing engine scene provider is not yet the UI's automatic-update contract.
// A drawing is closed for an actual model edit, then reopened. Only extract+step
// produce the new lines; the authored dimension records remain independent.
fn scene_snapshot(s: &mut Session, sheet: u64) -> (String, u64) {
    let first = crate::drawing_scene::extract(s, sheet).expect("extract real drawing scene");
    assert!(first.stale.len() == 1, "expected one view to be stale before provider step: {:?}", first.stale);
    let was = first.generation;
    while crate::drawing_scene::step(s) {}
    let now = crate::drawing_scene::extract(s, sheet).expect("extract after provider step");
    assert!(now.stale.is_empty(), "one top view should be fresh after step: {:?}", now.stale);
    assert!(now.generation > was, "provider didn't assemble a new scene");
    let d = s.drawing("test").expect("open original drawing").clone();
    let rebuilt = crate::drawing_scene::build(s, &d, sheet).expect("build whole scene");
    let actual = serde_json::to_string(now.scene.as_ref()).unwrap();
    let expected = serde_json::to_string(&rebuilt.scene).unwrap();
    assert_eq!(actual,expected,"provider step scene differs from freshly built scene");
    (actual,now.generation)
}

#[test]
fn w23a_t34_original_oracle84_lines_follow_bore10_to12_when_engine_provider_steps() {
    let mut f=plate_two_bores();
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let before=scene_snapshot(&mut f.session,sheet).0;
    let first=f.bore1.clone();
    f.change_bore1_to_12();
    let after=scene_snapshot(&mut f.session,sheet).0;
    assert_ne!(before,after,"true Ø10 -> Ø12 bore change must change projected scene lines");
    assert_ok(&inspect(&mut f.session,&first),12.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    println!("PASS: original Oracle84 Ø10 to Ø12 -> provider step draws current 2D scene lines matching build; dimension id preserved (no UI or annotations asserted)");
}

#[test]
fn w23a_t34_original_oracle84_deleted_bore_rebuilds_lines_and_undo_restores_scene() {
    let mut f=plate_two_bores();
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let baseline=scene_snapshot(&mut f.session,sheet).0;
    let first=f.bore1.clone();
    let second=f.bore2.clone();
    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session,158429.2036732051,"oracle 87 after delete");
    f.open();
    let deleted=scene_snapshot(&mut f.session,sheet).0;
    assert_ne!(deleted,baseline,"deleting Bore1 must alter the projected 2D lines");
    assert_eq!(inspect(&mut f.session,&first)["status"],json!("lost"));
    assert_ok(&inspect(&mut f.session,&second),10.0);
    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    assert_analytic_volume(&mut f.session,156858.4073464102,"oracle 84 undo");
    f.open();
    let restored=scene_snapshot(&mut f.session,sheet).0;
    assert_eq!(restored,baseline,"undo Bore1 must restore the original scene geometry");
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    println!("PASS: original Oracle84 Bore1 delete and undo changes/restores engine 2D scene lines, status lost/ok and dimension id retained");
}


fn add_second_front_view(f: &mut Plate) -> u64 {
    // The real A3 drawing from plate_two_bores() already owns a Top view.
    // Add a separate Front view, so we can verify independent freshness/step transitions.
    let mut d = (**f.session.drawing("test").expect("drawing open")).clone();
    let id = d.allocate_id(&mut IdSource::seeded(343434)).expect("second view id");
    let sheet = d.sheets[0].id;
    let source = d.sources[0].id;
    d.add_views([Arc::new(View {
        id, sheet,
        kind: ViewKind::Base { source, view: ViewDirection::Named(NamedView::Front) },
        place: ViewPlace::At([105.0, 100.0]),
        settings: ViewOverrides {
            scale: Some("1:2".parse().unwrap()), ..ViewOverrides::default()
        },
        reference_margin_mm: 0.0,
    })]);
    d.validate().expect("valid A3 drawing with two independent views");
    f.session.doc_mut().put_drawing(Arc::new(d));
    id
}

fn fresh_scene_bytes(s: &mut Session, sheet: u64, expected_views: usize) -> String {
    // Only read, never manually set freshness. The existing engine provider is the subject.
    let v = crate::drawing_scene::extract(s, sheet).expect("extract final scene");
    assert!(v.stale.is_empty(), "views still stale: {:?}", v.stale);
    assert_eq!(v.views.len(), expected_views, "unexpected number of drawn views");
    let d = s.drawing("test").expect("drawing still open");
    let rebuilt = crate::drawing_scene::build(s, d, sheet).expect("build actual current scene");
    let actual = serde_json::to_string(v.scene.as_ref()).unwrap();
    let expected = serde_json::to_string(&rebuilt.scene).unwrap();
    assert_eq!(actual, expected, "provider's incremental views differ from independently built scene");
    actual
}

#[test]
fn w23a_t34_two_view_incremental_updates_match_original_oracle84_after_diameter_edit() {
    let mut f = plate_two_bores();
    let _front = add_second_front_view(&mut f);
    let sheet = f.session.drawing("test").unwrap().sheets[0].id;
    let original = crate::drawing_scene::extract(&mut f.session, sheet).expect("first extract");
    assert_eq!(original.stale.len(), 2, "both views must start stale");
    assert_eq!(original.views.len(), 0, "no projected views before first engine step");

    assert!(crate::drawing_scene::step(&mut f.session), "first step should leave one view to draw");
    let half = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(half.stale.len(), 1, "one view should remain stale");
    assert_eq!(half.views.len(), 1, "one view should have been drawn");
    assert!(half.generation > original.generation, "first step did not advance scene generation");
    assert!(!crate::drawing_scene::step(&mut f.session), "second step must finish both views");
    let before = fresh_scene_bytes(&mut f.session, sheet, 2);

    // A real Sketch/Extrude/Hole model edit, while drawing closed, not an invented scene update.
    f.change_bore1_to_12();
    let still_open = f.session.drawing("test").expect("drawing reopened");
    assert_eq!(still_open.views.len(), 2, "model edit rewrote drawing view records");
    let initial = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(initial.stale.len(), 2, "reopened drawing must recompute both current views");
    assert_eq!(initial.views.len(), 0, "a fresh scene cache must not claim old model lines current");

    assert!(crate::drawing_scene::step(&mut f.session));
    let half = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(half.stale.len(), 1, "first step should update only one view");
    assert_eq!(half.views.len(), 1);
    assert!(!crate::drawing_scene::step(&mut f.session));
    let after = fresh_scene_bytes(&mut f.session, sheet, 2);
    assert_ne!(before, after, "Ø10→Ø12 must change the actual two-view paper scene");
    assert_ok(&inspect(&mut f.session, &f.bore1), 12.0);
    assert_ok(&inspect(&mut f.session, &f.bore2), 10.0);
    let repeated = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    let same_generation = repeated.generation;
    assert!(!crate::drawing_scene::step(&mut f.session), "no work should remain for stable views");
    let unchanged = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(unchanged.generation, same_generation);
    assert_eq!(unchanged.stale.len(), 0);
    println!("PASS: two original-model A3 views start stale, update exactly one per step, and final current lines match independent build after Bore1 Ø10→Ø12");
}

#[test]
fn w23a_t34_authored_text_edit_does_not_make_unmodified_view_geometry_stale() {
    let mut f = plate_two_bores();
    let sheet = f.session.drawing("test").unwrap().sheets[0].id;
    let initial = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(initial.stale.len(), 1);
    assert!(!crate::drawing_scene::step(&mut f.session));
    let before = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert!(before.stale.is_empty());
    let old_generation = before.generation;
    let old_lines = serde_json::to_string(before.scene.as_ref()).unwrap();
    let stable = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(stable.generation, old_generation);
    assert!(!crate::drawing_scene::step(&mut f.session));

    // Edit only authored text.at: this must not require a new projection of 3D geometry.
    let id = f.bore1.clone();
    let at = set_authored_text_at_paper(&mut f.session, &id, [95.0, 55.0], [205.0, 150.0]);
    assert_text_relative(&mut f.session, &id, at);
    let text_only = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert!(text_only.stale.is_empty(), "text place alone marked view geometry stale");
    assert_eq!(text_only.generation, old_generation, "text-only edit incorrectly redrew line scene");
    assert_eq!(serde_json::to_string(text_only.scene.as_ref()).unwrap(), old_lines);
    assert!(!crate::drawing_scene::step(&mut f.session));

    // In contrast, a real 3D width edit must generate different lines, and preserve text.at.
    f.close();
    let changed = run(&mut f.session, "parameters.change", json!({"name":"width","expression":"100 mm"}));
    assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()), "{changed}");
    assert_analytic_volume(&mut f.session, 196858.4073464102, "oracle85 after width edit");
    f.open();
    let stale = crate::drawing_scene::extract(&mut f.session, sheet).unwrap();
    assert_eq!(stale.stale.len(), 1, "geometry change must require a view recalculation");
    assert!(!crate::drawing_scene::step(&mut f.session));
    let current = fresh_scene_bytes(&mut f.session, sheet, 1);
    assert_ne!(current, old_lines, "geometry edit did not change paper view lines");
    assert_text_relative(&mut f.session, &id, at);
    assert_ok(&inspect(&mut f.session, &id), 10.0);
    assert_ok(&inspect(&mut f.session, &f.bore2), 10.0);
    println!("PASS: unchanged view does not reproject for dimension text.at-only edit; real oracle85 geometry edit invalidates and rebuilds the actual scene");
}
