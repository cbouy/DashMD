// load and display
var stringBlob = new Blob( [ "%s" ], { type: "text/plain" } );
// save some components to be restored
var orientation = stage.viewerControls.getOrientation();
// store which representations to activate
var show_repr = {
  0: 0,
  1: 0,
  2: 0,
  3: 0,
  4: 0,
};
for (i in repr.active) {
  show_repr[repr.active[i]] = 1;
}
// clean stage
stage.removeAllComponents();
// load structure
stage.loadFile(stringBlob, { ext: "pdb" } ).then(function (o) {
  // protein
  if (show_repr[0]) {
    o.addRepresentation("cartoon", {
      aspectRatio: 8,
      color: NGL.ColormakerRegistry.addSelectionScheme([["#59e500","protein"]], "Protein"),
    });
  }
  // ligand
  if (show_repr[1]) {
    o.addRepresentation("licorice", {
      sele: ligand_mask.value,
    });
  }
  // water
  if (show_repr[2]) {
    o.addRepresentation("licorice", {
      sele: "water and not hydrogen",
      opacity: 0.5,
    });
  }
  // lipids
  if (show_repr[3]) {
    o.addRepresentation("line", {
      sele: "not (protein or LIG or water or (K+ or Na+ or Cl- or ion)) and not hydrogen",
      opacity: 0.5,
      linewidth: 1.5,
    });
  }
  // ions
  if (show_repr[4]) {
    o.addRepresentation("ball+stick", {
      sele: "K+ or Na+ or Cl- or ion",
      aspectRatio: 3,
    });
  }

  o.autoView();
  stage.viewerControls.orient(orientation);
});
