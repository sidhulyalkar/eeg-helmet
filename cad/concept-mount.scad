// NEUROSHIELD CONCEPT ONLY -- NEVER INSTALL ON PROTECTIVE EQUIPMENT.
// Visualization fixture only: no certified clearances, stresses, retention,
// material properties, force response, manufacturability or safety validation.
$fn = 80;
travel_mm = 7.000;
plate_width = 46;
plate_height = 30;
plate_thick = 5;
module plate() {
    difference() {
      cube([plate_width,plate_height,plate_thick],center=true);
      for(x=[-15,15]) translate([x,0,0]) cylinder(h=10,d=6,center=true);
    }
}
color([0.16,0.38,0.63]) plate();
translate([0,0,9+travel_mm]) color([0.85,0.52,0.13]) plate();
for (x=[-15,15]) translate([x,0,3]) color([0.32,0.75,0.67])
 cylinder(h=6+travel_mm, d=3);
