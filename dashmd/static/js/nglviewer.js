// Set up NGL Viewport and data registry
if (!document.getElementById('nglviewport')) {
    // Create viewport div
    var vp = document.createElement('div');
    vp.setAttribute("id", "nglviewport");
    vp.setAttribute("style", "height: 700px;")
    // Insert it inside the ngldiv Div
    var ngldiv = document.getElementsByClassName('ngldiv')[0];
    ngldiv.appendChild(vp)
}
// Create NGL Stage object
var stage = new NGL.Stage( "nglviewport" );
// Handle window resizing
window.addEventListener( "resize", function( event ){
    stage.handleResize();
}, false );
// load and display
var stringBlob = new Blob( [ "%s" ], { type: "text/plain" } );
NGL.autoLoad(stringBlob, { ext: "pdb" } ).then(function (structure) {
  var o = stage.addComponentFromObject(structure);
  o.addRepresentation("cartoon", {
    aspectRatio: 8,
    color: NGL.ColormakerRegistry.addSelectionScheme([["#59e500","protein"]], "Protein"),
  });
  o.addRepresentation("licorice", {
    sele: "ligand and not hydrogen",
    opacity: 0.8,
  });
  o.addRepresentation("spacefill", {
    sele: "ion",
  });
  o.addRepresentation("licorice", {
    sele: "water and not hydrogen",
    opacity: 0.5
  });
  stage.autoView();
})
