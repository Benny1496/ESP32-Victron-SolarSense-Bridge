//! Test 40 (external harness): real model-command-to-drawing inspect probes for W23a.
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
    let source = std::fs::read_to_string(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../ci-reports/w23a-test40/oracle84-commands.json"))
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
    run(&mut s, "drawing.create", json!({"name":"W23a test40"}));
    let mut d = (**s.drawing("test40").expect("open drawing")).clone();
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
fn w23a_t40_bore1_10_to_12_keeps_dimension_id_and_independent_bore2() {
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
fn w23a_t40_deleted_bore1_is_lost_never_bore2_then_undo() {
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
fn w23a_t40_original_oracle84_change_undo_redo_preserves_measure_identity() {
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
fn w23a_t40_oracle85_width_80_to_100_preserves_two_hole_dimensions_and_undo_redo() {
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
fn w23a_t40_user_authored_sheet_text_positions_survive_diameter_edit_and_undo_redo() {
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
fn w23a_t40_deleted_bore1_lost_then_undo_then_redo_preserves_authored_text_and_other_hole() {
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
fn w23a_t40_original_oracle84_lines_follow_bore10_to12_when_engine_provider_steps() {
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
fn w23a_t40_original_oracle84_deleted_bore_rebuilds_lines_and_undo_restores_scene() {
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
fn w23a_t40_two_view_incremental_updates_match_original_oracle84_after_diameter_edit() {
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
fn w23a_t40_authored_text_edit_does_not_make_unmodified_view_geometry_stale() {
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


fn public_drawing_scene(s: &mut Session, sheet: u64, count: usize) -> Value {
    // This is the user-visible drawing.scene command, rather than the internal provider API.
    let answer = run(s, "drawing.scene", json!({"sheet": ids::encode(sheet)}));
    assert_eq!(answer["sheet"], json!(ids::encode(sheet)));
    let views = answer["views"].as_array().expect("public scene must contain view states");
    assert_eq!(views.len(), count, "missing view states: {answer}");
    assert!(views.iter().all(|v| v["status"] == "drawn"), "{answer}");
    assert!(answer["scene"]["groups"].as_array().is_some_and(|g| !g.is_empty()), "empty public scene: {answer}");
    answer
}

fn public_scene_matches_engine_provider(s: &mut Session, sheet: u64, count: usize) -> String {
    let public = public_drawing_scene(s, sheet, count);
    let _initial = crate::drawing_scene::extract(s, sheet).expect("extract");
    while crate::drawing_scene::step(s) {}
    let settled = crate::drawing_scene::extract(s, sheet).expect("settled");
    assert!(settled.stale.is_empty(), "provider stale after steps");
    assert_eq!(settled.views.len(), count);
    let source = serde_json::to_value(settled.scene.as_ref()).unwrap();
    assert_eq!(public["scene"],source,"public drawing.scene command and engine provider disagree");
    serde_json::to_string(&source).unwrap()
}

#[test]
fn w23a_t40_public_drawing_scene_matches_two_views_after_bore_parameter_edit() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let base=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    let a=f.bore1.clone();
    f.change_bore1_to_12();
    let modified=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(base,modified,"original model Ø10→Ø12 must change public 2D drawing output");
    let first=inspect(&mut f.session,&a);
    assert_eq!(first["dimension"],a);
    assert_ok(&first,12.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    println!("PASS: public drawing.scene shows changed two-view 2D lines for original oracle84, and matches incremental engine after Ø10→Ø12");
}

#[test]
fn w23a_t40_public_drawing_scene_undo_and_redo_return_to_exact_prior_paper_lines() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let first=f.bore1.clone();
    let second=f.bore2.clone();
    let baseline=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    f.close();
    let changed=run(&mut f.session,"parameters.change",json!({"name":"width","expression":"100 mm"}));
    assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()),"{changed}");
    assert_analytic_volume(&mut f.session,196858.4073464102,"oracle85 width");
    f.open();
    let wider=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(baseline,wider,"Oracle85 width=100 should change public 2D scene");
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    assert_analytic_volume(&mut f.session,156858.4073464102,"oracle84 restored");
    f.open();
    let restored=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_eq!(baseline,restored,"undo must reproduce exactly the original sheet output");
    f.close();
    run(&mut f.session,"edit.redo",json!({}));
    assert_analytic_volume(&mut f.session,196858.4073464102,"oracle85 again");
    f.open();
    let redone=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_eq!(wider,redone,"redo must reproduce exactly the previously changed sheet");
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    println!("PASS: public drawing.scene, two real views and authored hole dimensions follow width 80→100, undo and redo without geometry drift");
}


#[test]
fn w23a_t40_public_two_view_delete_undo_redo_stays_lost_without_rebinding() {
    let mut f = plate_two_bores();
    let _front = add_second_front_view(&mut f);
    let sheet = f.session.drawing("test").unwrap().sheets[0].id;
    let first = f.bore1.clone();
    let second = f.bore2.clone();
    let original = public_scene_matches_engine_provider(&mut f.session, sheet, 2);

    f.close();
    run(&mut f.session, "timeline.delete", json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session, 158429.2036732051, "oracle 87 delete Bore1");
    f.open();
    let deleted = public_scene_matches_engine_provider(&mut f.session, sheet, 2);
    assert_ne!(original, deleted, "deleting Bore1 must remove lines from public scene");
    let lost = inspect(&mut f.session, &first);
    assert_eq!(lost["dimension"], first, "deleted dimension ID changed");
    assert_eq!(lost["status"], "lost", "Bore1 must be lost, not assigned to Bore2");
    assert!(lost.get("value").is_none(), "a lost dimension must not present a live value");
    assert_ok(&inspect(&mut f.session, &second), 10.0);

    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    assert_analytic_volume(&mut f.session, 156858.4073464102, "oracle 84 undo Bore1 delete");
    f.open();
    let restored = public_scene_matches_engine_provider(&mut f.session, sheet, 2);
    assert_eq!(original, restored, "undo must restore public 2D lines exactly");
    assert_ok(&inspect(&mut f.session, &first), 10.0);
    assert_ok(&inspect(&mut f.session, &second), 10.0);

    f.close();
    run(&mut f.session, "edit.redo", json!({}));
    assert_analytic_volume(&mut f.session, 158429.2036732051, "oracle 87 redo Bore1 delete");
    f.open();
    let again = public_scene_matches_engine_provider(&mut f.session, sheet, 2);
    assert_eq!(deleted, again, "redo must restore the deleted-hole 2D scene exactly");
    let again_lost = inspect(&mut f.session, &first);
    assert_eq!(again_lost["dimension"], first);
    assert_eq!(again_lost["status"], "lost");
    assert_ok(&inspect(&mut f.session, &second), 10.0);
    println!("PASS: public two-view drawing.scene after Bore1 delete/undo/redo matches exact 2D states; Bore1 stays lost without rebinding to Bore2");
}

#[test]
fn w23a_t40_sequential_width_and_bore_edits_undo_twice_redo_twice_restore_public_views() {
    let mut f = plate_two_bores();
    let _front = add_second_front_view(&mut f);
    let sheet = f.session.drawing("test").unwrap().sheets[0].id;
    let id1 = f.bore1.clone();
    let id2 = f.bore2.clone();
    let original = public_scene_matches_engine_provider(&mut f.session, sheet, 2);

    f.close();
    let width = run(&mut f.session, "parameters.change", json!({"name":"width","expression":"100 mm"}));
    assert!(width["errors"].as_array().is_some_and(|a| a.is_empty()), "{width}");
    assert_analytic_volume(&mut f.session, 196858.4073464102, "oracle 85 width 100");
    f.open();
    let wider = public_scene_matches_engine_provider(&mut f.session, sheet, 2);
    assert_ne!(original, wider);
    assert_ok(&inspect(&mut f.session, &id1), 10.0);
    assert_ok(&inspect(&mut f.session, &id2), 10.0);

    f.close();
    let bore = run(&mut f.session, "parameters.change", json!({"name":"bore1_d","expression":"12 mm"}));
    assert!(bore["errors"].as_array().is_some_and(|a| a.is_empty()), "{bore}");
    assert_analytic_volume(&mut f.session, 196167.25696262045, "100 wide with Bore1 diameter 12");
    f.open();
    let wider_bore = public_scene_matches_engine_provider(&mut f.session, sheet, 2);
    assert_ne!(wider, wider_bore);
    assert_ok(&inspect(&mut f.session, &id1), 12.0);
    assert_ok(&inspect(&mut f.session, &id2), 10.0);

    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    assert_analytic_volume(&mut f.session, 196858.4073464102, "undo Bore1 only");
    f.open();
    assert_eq!(wider, public_scene_matches_engine_provider(&mut f.session, sheet, 2));
    assert_ok(&inspect(&mut f.session, &id1), 10.0);

    f.close();
    run(&mut f.session, "edit.undo", json!({}));
    assert_analytic_volume(&mut f.session, 156858.4073464102, "undo width");
    f.open();
    assert_eq!(original, public_scene_matches_engine_provider(&mut f.session, sheet, 2));
    assert_ok(&inspect(&mut f.session, &id1), 10.0);

    f.close();
    run(&mut f.session, "edit.redo", json!({}));
    assert_analytic_volume(&mut f.session, 196858.4073464102, "redo width");
    f.open();
    assert_eq!(wider, public_scene_matches_engine_provider(&mut f.session, sheet, 2));

    f.close();
    run(&mut f.session, "edit.redo", json!({}));
    assert_analytic_volume(&mut f.session, 196167.25696262045, "redo Bore1");
    f.open();
    assert_eq!(wider_bore, public_scene_matches_engine_provider(&mut f.session, sheet, 2));
    let last1 = inspect(&mut f.session, &id1);
    assert_eq!(last1["dimension"], id1);
    assert_ok(&last1, 12.0);
    let last2 = inspect(&mut f.session, &id2);
    assert_eq!(last2["dimension"], id2);
    assert_ok(&last2, 10.0);
    println!("PASS: public drawing.scene two-view output and separate hole IDs survive width + Bore1 consecutive edits, double undo and double redo");
}


fn assert_lost_with_session_last_good(reply: &Value, id: &Value, historical: f64) {
    assert_eq!(reply["dimension"], *id, "a lost record must preserve its identity: {reply}");
    assert_eq!(reply["status"], json!("lost"), "lost record must not silently bind elsewhere: {reply}");
    assert!(reply.get("value").is_none(), "a lost reference must have no live measured value: {reply}");
    let observed=reply["last_good"].as_f64().unwrap_or_else(||
        panic!("missing last good session value from a previously measured dimension: {reply}"));
    assert!((observed-historical).abs()<1e-8, "last_good incorrectly changed: expected {historical}, got {observed}");
}

#[test]
fn w23a_t40_last_good_12_mm_stays_with_lost_dimension_through_delete_undo_redo() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let id=f.bore1.clone();
    let other=f.bore2.clone();
    let at=set_authored_text_at_paper(&mut f.session,&id,[95.0,55.0],[205.0,150.0]);
    assert_ok(&inspect(&mut f.session,&id),10.0);
    f.change_bore1_to_12();
    let valid=inspect(&mut f.session,&id);
    assert_eq!(valid["dimension"],id);
    assert_ok(&valid,12.0);
    assert_text_relative(&mut f.session,&id,at);
    let scene_valid=public_scene_matches_engine_provider(&mut f.session,sheet,2);

    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session,160000.0 - std::f64::consts::PI * 5.0 * 5.0 * 20.0,"one remaining Bore2");
    f.open();
    let scene_lost=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(scene_valid,scene_lost);
    let lost=inspect(&mut f.session,&id);
    assert_lost_with_session_last_good(&lost,&id,12.0);
    assert_text_relative(&mut f.session,&id,at);
    assert_ok(&inspect(&mut f.session,&other),10.0);
    assert!(lost["record"].get("historical_last_value_mm").is_none(),
        "this pinned source has NO persisted historical_last_value_mm: {lost}");

    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_eq!(scene_valid,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_ok(&inspect(&mut f.session,&id),12.0);
    assert_text_relative(&mut f.session,&id,at);

    f.close();
    run(&mut f.session,"edit.redo",json!({}));
    f.open();
    assert_eq!(scene_lost,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_lost_with_session_last_good(&inspect(&mut f.session,&id),&id,12.0);
    assert_ok(&inspect(&mut f.session,&other),10.0);
    assert_text_relative(&mut f.session,&id,at);
    println!("PASS: actual original Oracle84 Bore1 Ø12 read then deleted retains last_good=12 in session across undo/redo, not a persisted file; public 2D scenes and text record remain coherent");
}

#[test]
fn w23a_t40_two_independent_lost_dimensions_undo_in_reverse_order_never_rebind() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let first=f.bore1.clone();
    let second=f.bore2.clone();
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    let original=public_scene_matches_engine_provider(&mut f.session,sheet,2);

    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session,158429.2036732051,"oracle87 one bore missing");
    f.open();
    let only_second=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(original,only_second);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);

    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore2"}));
    assert_analytic_volume(&mut f.session,160000.0,"both bores removed, full plate volume");
    f.open();
    let both_lost=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(only_second,both_lost);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,10.0);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&second),&second,10.0);

    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    assert_analytic_volume(&mut f.session,158429.2036732051,"restore second bore only");
    f.open();
    assert_eq!(only_second,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);

    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    assert_analytic_volume(&mut f.session,156858.4073464102,"restore both holes");
    f.open();
    assert_eq!(original,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);

    println!("PASS: delete two independent bores, see two separate lost+session-last_good dimensions and distinct public 2D scenes, then undo in order without rebinding to other hole");
}


#[test]
fn w23a_t40_two_changed_bores_keep_distinct_session_last_good_12_and_8_after_both_are_deleted() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let first=f.bore1.clone();
    let second=f.bore2.clone();
    f.change_bore1_to_12();
    assert_ok(&inspect(&mut f.session,&first),12.0);

    f.close();
    let changed=run(&mut f.session,"parameters.change",json!({"name":"bore2_d","expression":"8 mm"}));
    assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()),"{changed}");
    let analytic=156858.4073464102 + std::f64::consts::PI * 20.0 * (25.0-16.0) -
                 std::f64::consts::PI * 20.0 * (36.0-25.0);
    assert_analytic_volume(&mut f.session,analytic,"original Oracle84 Bore1 diameter 12 and Bore2 diameter 8");
    f.open();
    assert_ok(&inspect(&mut f.session,&first),12.0);
    assert_ok(&inspect(&mut f.session,&second),8.0);
    let both_changed=public_scene_matches_engine_provider(&mut f.session,sheet,2);

    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    assert_analytic_volume(&mut f.session,160000.0-std::f64::consts::PI*16.0*20.0,"Bore1 deleted, Bore2 diameter 8");
    f.open();
    let one_lost=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(both_changed,one_lost);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,12.0);
    assert_ok(&inspect(&mut f.session,&second),8.0);

    f.close();
    run(&mut f.session,"timeline.delete",json!({"feature":"Bore2"}));
    assert_analytic_volume(&mut f.session,160000.0,"both changed bores deleted");
    f.open();
    let both_lost=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(one_lost,both_lost);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,12.0);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&second),&second,8.0);

    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_eq!(one_lost,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,12.0);
    assert_ok(&inspect(&mut f.session,&second),8.0);

    f.close();
    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_eq!(both_changed,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    let restored1=inspect(&mut f.session,&first);
    let restored2=inspect(&mut f.session,&second);
    assert_eq!(restored1["dimension"],first);
    assert_eq!(restored2["dimension"],second);
    assert_ok(&restored1,12.0);
    assert_ok(&restored2,8.0);
    println!("PASS: real W23a independent diameters 12 and 8 retain distinct session last_good after both holes are deleted and undone, no silent remapping");
}

#[test]
fn w23a_t40_last_good_replaces_old_12_with_newly_measured_11_before_hole_is_lost() {
    let mut f=plate_two_bores();
    let id=f.bore1.clone();
    assert_ok(&inspect(&mut f.session,&id),10.0);
    f.change_bore1_to_12();
    assert_ok(&inspect(&mut f.session,&id),12.0);

    f.close();
    let changed=run(&mut f.session,"parameters.change",json!({"name":"bore1_d","expression":"11 mm"}));
    assert!(changed["errors"].as_array().is_some_and(|a| a.is_empty()),"{changed}");
    let analytic=156858.4073464102 - std::f64::consts::PI *20.0*(5.5*5.5-5.0*5.0);
    assert_analytic_volume(&mut f.session,analytic,"Bore1 revised diameter 11");
    f.open();
    let current=inspect(&mut f.session,&id);
    assert_eq!(current["dimension"],id);
    assert_ok(&current,11.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    f.close();

    run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));
    f.open();
    let lost=inspect(&mut f.session,&id);
    assert_lost_with_session_last_good(&lost,&id,11.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    f.close();

    run(&mut f.session,"edit.undo",json!({}));
    f.open();
    assert_ok(&inspect(&mut f.session,&id),11.0);
    f.close();

    run(&mut f.session,"edit.redo",json!({}));
    f.open();
    assert_lost_with_session_last_good(&inspect(&mut f.session,&id),&id,11.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    println!("PASS: last_good follows the latest actually measured 11mm value, not stale 12mm, after deleting and undoing/redoing Bore1 (session only)");
}


// CamWight #4892/#3890: drawing and its design live in one document.
// This is a native-session open/close test, NOT a file-save/reopen claim.
fn current_drawing_record(f: &Plate) -> Value {
    serde_json::to_value(&**f.session.drawing("test").expect("drawing open")).unwrap()
}
fn set_model_params(f: &mut Plate, params: &[(&str, f64)]) {
    f.close();
    for (name, value) in params {
        let answer = run(&mut f.session,"parameters.change",
            json!({"name":name,"expression":format!("{value} mm")}));
        assert!(answer["errors"].as_array().is_some_and(|errors|errors.is_empty()),
            "model parameter {name}={value} failed: {answer}");
    }
    f.open();
}
fn model_undo_steps(f: &mut Plate, count: usize, redo: bool) {
    f.close();
    for _ in 0..count {
        run(&mut f.session,if redo {"edit.redo"}else{"edit.undo"},json!({}));
    }
    f.open();
}
fn analytic_plate(width: f64, d1: f64, d2: f64) -> f64 {
    100.0*width*20.0-std::f64::consts::PI*20.0*((d1/2.0).powi(2)+(d2/2.0).powi(2))
}
// Measurement is a MODEL command; SolidCraft refuses it while a drawing is open.
// Keep the original numeric assertion, but obey the real public command lifecycle.
// Reopening must preserve the drawing record, IDs and subsequent inspect assertions.
fn assert_analytic_volume_with_drawing(f: &mut Plate, reference: f64, oracle: &str) {
    f.close();
    assert_analytic_volume(&mut f.session, reference, oracle);
    f.open();
}

fn w40_oracle_matrix_case(width:f64,d1:f64,d2:f64) {
    assert_ne!(width,80.0);assert_ne!(d1,10.0);assert_ne!(d2,10.0);
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let id1=f.bore1.clone();
    let id2=f.bore2.clone();
    let drawing_before=current_drawing_record(&f);
    let original=public_scene_matches_engine_provider(&mut f.session,sheet,2);

    // Three separate model commands in ONE design; drawing closed during changes.
    set_model_params(&mut f,&[("width",width),("bore1_d",d1),("bore2_d",d2)]);
    assert_analytic_volume_with_drawing(&mut f,analytic_plate(width,d1,d2),"matrix changed exact source volume");
    let changed=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(original,changed,"public 2D scene did not change after real 3D edits");
    assert_eq!(drawing_before,current_drawing_record(&f),"model edits changed the stored drawing record");
    let r1=inspect(&mut f.session,&id1);let r2=inspect(&mut f.session,&id2);
    assert_eq!(r1["dimension"],id1);assert_eq!(r2["dimension"],id2);
    assert_ok(&r1,d1);assert_ok(&r2,d2);

    // Shared model undo must NOT undo/replace the drawing embedded in design.
    model_undo_steps(&mut f,3,false);
    assert_analytic_volume_with_drawing(&mut f,analytic_plate(80.0,10.0,10.0),"matrix 3 model undos");
    assert_eq!(original,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_eq!(drawing_before,current_drawing_record(&f),"model undo lost the drawing");
    assert_ok(&inspect(&mut f.session,&id1),10.0);
    assert_ok(&inspect(&mut f.session,&id2),10.0);

    model_undo_steps(&mut f,3,true);
    assert_analytic_volume_with_drawing(&mut f,analytic_plate(width,d1,d2),"matrix 3 model redos");
    assert_eq!(changed,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_eq!(drawing_before,current_drawing_record(&f),"model redo lost the drawing");
    assert_ok(&inspect(&mut f.session,&id1),d1);
    assert_ok(&inspect(&mut f.session,&id2),d2);
    println!("PASS: Oracle84 matrix width={width} Ø1={d1} Ø2={d2}, 2 public scenes, 3 model undos/3 redos, stored drawing unchanged, IDs stable");
}
macro_rules! w40_matrix {
    ($name:ident,$w:expr,$a:expr,$b:expr) => {
        #[test]
        fn $name(){w40_oracle_matrix_case($w,$a,$b);}
    };
}
// 16 real independent original-Oracle84 builds, six model-edit/undo/redo steps each.
w40_matrix!(w23a_t40_matrix_01_w85_a8_b12,85.0,8.0,12.0);
w40_matrix!(w23a_t40_matrix_02_w85_a12_b8,85.0,12.0,8.0);
w40_matrix!(w23a_t40_matrix_03_w85_a6_b14,85.0,6.0,14.0);
w40_matrix!(w23a_t40_matrix_04_w85_a14_b6,85.0,14.0,6.0);
w40_matrix!(w23a_t40_matrix_05_w95_a8_b14,95.0,8.0,14.0);
w40_matrix!(w23a_t40_matrix_06_w95_a14_b8,95.0,14.0,8.0);
w40_matrix!(w23a_t40_matrix_07_w95_a6_b12,95.0,6.0,12.0);
w40_matrix!(w23a_t40_matrix_08_w95_a12_b6,95.0,12.0,6.0);
w40_matrix!(w23a_t40_matrix_09_w110_a8_b6,110.0,8.0,6.0);
w40_matrix!(w23a_t40_matrix_10_w110_a6_b8,110.0,6.0,8.0);
w40_matrix!(w23a_t40_matrix_11_w110_a12_b14,110.0,12.0,14.0);
w40_matrix!(w23a_t40_matrix_12_w110_a14_b12,110.0,14.0,12.0);
w40_matrix!(w23a_t40_matrix_13_w120_a8_b14,120.0,8.0,14.0);
w40_matrix!(w23a_t40_matrix_14_w120_a14_b8,120.0,14.0,8.0);
w40_matrix!(w23a_t40_matrix_15_w120_a6_b12,120.0,6.0,12.0);
w40_matrix!(w23a_t40_matrix_16_w120_a12_b6,120.0,12.0,6.0);

#[test]
fn w23a_t40_model_change_is_rejected_while_drawing_open_without_mutating_design() {
    let mut f=plate_two_bores();
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let scene=public_scene_matches_engine_provider(&mut f.session,sheet,1);
    let before=current_drawing_record(&f);
    let attempt=f.session.execute("parameters.change",&json!({"name":"width","expression":"100 mm"}));
    assert!(attempt.is_err(),"model command should be refused while drawing is open");
    assert_eq!(current_drawing_record(&f),before);
    assert_eq!(scene,public_scene_matches_engine_provider(&mut f.session,sheet,1));
    assert_ok(&inspect(&mut f.session,&f.bore1),10.0);
    assert_ok(&inspect(&mut f.session,&f.bore2),10.0);
    f.close();
    assert_analytic_volume(&mut f.session,156858.4073464102,"refused change leaves original model");
    println!("PASS: model commands blocked while own drawing is open; both drawing and 3D model unchanged");
}

#[test]
fn w23a_t40_one_design_drawing_record_survives_model_undo_and_redo() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let record=current_drawing_record(&f);
    let baseline=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    set_model_params(&mut f,&[("width",100.0)]);
    assert_eq!(record,current_drawing_record(&f),"drawing vanished from the design after edit");
    let modified=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(baseline,modified);
    model_undo_steps(&mut f,1,false);
    assert_eq!(record,current_drawing_record(&f),"model undo rolled back drawing record");
    assert_eq!(baseline,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    model_undo_steps(&mut f,1,true);
    assert_eq!(record,current_drawing_record(&f),"model redo replaced drawing record");
    assert_eq!(modified,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    println!("PASS: drawing remains in same design record through model change and undo/redo, two on-demand scenes correct");
}

#[test]
fn w23a_t40_open_close_open_cycles_keep_one_record_and_dimension_identities() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let record=current_drawing_record(&f);
    let expected=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    let id1=f.bore1.clone();let id2=f.bore2.clone();
    for cycle in 0..5 {
        f.close();f.open();
        assert_eq!(record,current_drawing_record(&f),"reopening changed stored drawing at cycle {cycle}");
        assert_eq!(expected,public_scene_matches_engine_provider(&mut f.session,sheet,2));
        assert_ok(&inspect(&mut f.session,&id1),10.0);
        assert_ok(&inspect(&mut f.session,&id2),10.0);
    }
    println!("PASS: five close/reopen cycles retain the drawing inside its design and regenerate identical 2D scenes; NOT file save/reopen");
}

#[test]
fn w23a_t40_authored_text_record_is_not_undone_by_separate_model_undo() {
    let mut f=plate_two_bores();
    let first=f.bore1.clone();
    set_model_params(&mut f,&[("width",100.0)]);
    let at=set_authored_text_at_paper(&mut f.session,&first,[95.0,55.0],[205.0,150.0]);
    assert_text_relative(&mut f.session,&first,at);
    let edited=current_drawing_record(&f);
    model_undo_steps(&mut f,1,false);
    assert_eq!(edited,current_drawing_record(&f),"undoing MODEL must not undo authored drawing edit");
    assert_text_relative(&mut f.session,&first,at);
    assert_ok(&inspect(&mut f.session,&first),10.0);
    model_undo_steps(&mut f,1,true);
    assert_eq!(edited,current_drawing_record(&f));
    assert_text_relative(&mut f.session,&first,at);
    println!("PASS: authored text.at drawing record retained when a separate model change is undone and redone");
}

#[test]
fn w23a_t40_reverse_delete_order_never_attaches_diameter_to_other_hole() {
    let mut f=plate_two_bores();
    let _front=add_second_front_view(&mut f);
    let sheet=f.session.drawing("test").unwrap().sheets[0].id;
    let original=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    let first=f.bore1.clone();let second=f.bore2.clone();
    f.close();run(&mut f.session,"timeline.delete",json!({"feature":"Bore2"}));f.open();
    let only_first=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(original,only_first);
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&second),&second,10.0);
    f.close();run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));f.open();
    let both_gone=public_scene_matches_engine_provider(&mut f.session,sheet,2);
    assert_ne!(only_first,both_gone);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&first),&first,10.0);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&second),&second,10.0);
    model_undo_steps(&mut f,1,false);
    assert_eq!(only_first,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_lost_with_session_last_good(&inspect(&mut f.session,&second),&second,10.0);
    model_undo_steps(&mut f,1,false);
    assert_eq!(original,public_scene_matches_engine_provider(&mut f.session,sheet,2));
    assert_ok(&inspect(&mut f.session,&first),10.0);
    assert_ok(&inspect(&mut f.session,&second),10.0);
    println!("PASS: deleting Bore2 first and Bore1 second preserves separate IDs and lost status in reverse order");
}

#[test]
fn w23a_t40_last_good_values_stay_separate_across_unrelated_width_edits() {
    let mut f=plate_two_bores();let a=f.bore1.clone();let b=f.bore2.clone();
    set_model_params(&mut f,&[("bore1_d",12.0),("bore2_d",8.0)]);
    assert_ok(&inspect(&mut f.session,&a),12.0);
    assert_ok(&inspect(&mut f.session,&b),8.0);
    set_model_params(&mut f,&[("width",95.0),("width",110.0)]);
    assert_analytic_volume_with_drawing(&mut f,analytic_plate(110.0,12.0,8.0),"independent width edits");
    assert_ok(&inspect(&mut f.session,&a),12.0);
    assert_ok(&inspect(&mut f.session,&b),8.0);
    f.close();run(&mut f.session,"timeline.delete",json!({"feature":"Bore1"}));f.open();
    assert_lost_with_session_last_good(&inspect(&mut f.session,&a),&a,12.0);
    assert_ok(&inspect(&mut f.session,&b),8.0);
    println!("PASS: two unrelated width edits preserve last_good and reference identity of unequal bore dimensions");
}
