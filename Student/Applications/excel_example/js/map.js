var map, identifyListener;

require([
    "esri/map", "esri/dijit/BasemapGallery", "esri/arcgis/utils",
    "esri/layers/ArcGISDynamicMapServiceLayer",
    "esri/symbols/SimpleFillSymbol",
    "esri/symbols/SimpleLineSymbol",
    "esri/toolbars/draw",
    "esri/graphic",
    "esri/request",
    "esri/Color",
    "esri/tasks/Geoprocessor",
    "esri/tasks/FeatureSet",
	"esri/layers/FeatureLayer",
    "esri/dijit/Search",
    "esri/InfoTemplate",
	"esri/dijit/Popup",
	"esri/dijit/PopupTemplate",
    "esri/tasks/IdentifyTask",
    "esri/tasks/IdentifyParameters",
    "dojo/parser",
    "dojo/dom",
    "dojo/on",
    "dojo/_base/array",
    "dojo/_base/json",
    "dojo/dom-construct",
    "dijit/form/Button",
    "dojo/dom-construct",
    "dijit/form/ComboBox",
    "dijit/form/ToggleButton",
    "dijit/layout/BorderContainer", "dijit/layout/ContentPane", "dijit/TitlePane",
    "dojo/domReady!"
], function(Map, BasemapGallery, arcgisUtils,
    agsDynMS,
    SimpleFillSymbol,
    SimpleLineSymbol,
    Draw,
    Graphic,
    esriRequest,
    Color,
    Geoprocessor,
    FeatureSet,
	FeatureLayer,
    Search,
    InfoTemplate,
	Popup,
	PopupTemplate,
    IdentifyTask,
    IdentifyParameters,
    parser,
    dom,
    on,
    arrayUtils,
    dojoJSON,
    domConstruct,
    Button,
    domConstruct,
    ComboBox,
    ToggleButton

) {
	// read dojo specific dijits
    parser.parse();
	
	// popup template for info window
	var popup = new Popup({
	  fillSymbol: new SimpleFillSymbol(SimpleFillSymbol.STYLE_SOLID,
		new SimpleLineSymbol(SimpleLineSymbol.STYLE_SOLID,
		  new Color([255, 0, 0]), 2), new Color([255, 255, 0, 0.25]))
	}, domConstruct.create("div"));
	
	var geometryInput, identifyParams, identifyTask
	
    map = new Map("map", {
        basemap: "satellite",
        center: [-93.77, 44.61],
        zoom: 14,
		infoWindow: popup,
        slider: true
    });
	
    // add dynamic map service
    var bellUrl = "http://lt0212x1g2676:6080/arcgis/rest/services/BELL/Bell_Webmap_REST/MapServer";
    var bell = new agsDynMS(bellUrl);
	
	// add feature layers
	hydPop = new PopupTemplate({
            title: "Hydrant Number: {HYD_NUM}",
            fieldInfos: [
              {
                fieldName: "PROJ_NUM",
                visible: true,
                label: "Project Number"
              },
              {
                fieldName: "CONDITION",
                visible: true,
                label: "Condition",
              },
            ],
            showAttachments: true
          });
		  
	culPop = new PopupTemplate({
            title: "Culvert Number: {CULV_NUM}",
            fieldInfos: [
              {
                fieldName: "CULV_SIZE",
                visible: true,
                label: "Size:"
              },
              {
                fieldName: "CULV_MAT",
                visible: true,
                label: "Material:",
              },
            ],
            showAttachments: true
          });
							
	var hydrants = new FeatureLayer("http://lt0212x1g2676:6080/arcgis/rest/services/BELL/Editor/FeatureServer/0", {
		mode: FeatureLayer.MODE_ONDEMAND,
		infoTemplate: hydPop,
		outFields: ["*"],
		id: "hydrants"});
		
	var culverts = new FeatureLayer("http://lt0212x1g2676:6080/arcgis/rest/services/BELL/Editor/FeatureServer/1", {
		mode: FeatureLayer.MODE_ONDEMAND,
		infoTemplate: culPop,
		outFields: ["*"]});
	map.addLayers([bell, hydrants, culverts]);

    // add toggle for Identify
    var toggleID = new ToggleButton({
        showLabel: true,
        checked: false,
        onChange: function() {
            if (this.checked) {
                this.set('label', 'Disable Identify')
            } else {
                this.set('label', 'Enable Identify')
            }
            activateIdentify()
        },
        label: "Enable Identify"
    }, "tool_identify");
    toggleID.startup();

    map.on("load", mapReady);

    // event listener for identify tool
    function activateIdentify() {
        if (toggleID.checked) {
            identifyListener = dojo.connect(map, "onClick", executeIdentifyTask);
        } else {
            dojo.disconnect(identifyListener);
        }
    }

    // set up identify params <- from esri sample
    function mapReady() {
        //create identify tasks and setup parameters
        identifyTask = new IdentifyTask(bellUrl);

        identifyParams = new IdentifyParameters();
        identifyParams.tolerance = 3;
        identifyParams.returnGeometry = true;
        identifyParams.layerIds = [6];
        identifyParams.layerOption = IdentifyParameters.LAYER_OPTION_ALL;
        identifyParams.width = map.width;
        identifyParams.height = map.height;
    };

    // identify features <- from esri sample
    function executeIdentifyTask(event) {
        identifyParams.geometry = event.mapPoint;
        identifyParams.mapExtent = map.extent;

        var deferred = identifyTask
            .execute(identifyParams)
            .addCallback(function(response) {
                // response is an array of identify result objects
                return arrayUtils.map(response, function(result) {
                    var feature = result.feature;
                    var layerName = result.layerName;

                    feature.attributes.layerName = layerName;
                    if (layerName === 'Parcels') {
                        var taxParcelTemplate = new InfoTemplate("Parcel ID: ${Parcel ID}",
                            "Owner Name: ${Owner Name} <br/> Address: ${Property Address}");
                        feature.setInfoTemplate(taxParcelTemplate);
                    }
                    return feature;
                });
            });

        map.infoWindow.setFeatures([deferred]);
        map.infoWindow.show(event.mapPoint);
    };
	
	// dialog control for gp task
	on(dom.byId("openGpDialog"), "click", showDialog);
	on(dom.byId("gpCancel"), "click", dlgHide);
	on(dom.byId("gpOK"), "click", exportExcel);
	
    function dlgHide(){
        var whitebg = dom.byId("white-background");
        var dlg = dom.byId("dlgbox");
        whitebg.style.display = "none";
        dlg.style.display = "none";
    }
    function showDialog(){
        var whitebg = dom.byId("white-background");
        var dlg = dom.byId("dlgbox");
        whitebg.style.display = "block";
        dlg.style.display = "block";
        var winWidth = window.innerWidth;
        dlg.style.left = (winWidth/2) - 480/2 + "px";
        dlg.style.top = "150px";
    }

    // add the basemap gallery
    var basemapGallery = new BasemapGallery({
        showArcGISBasemaps: true,
        map: map
    }, "basemapGallery");
    basemapGallery.startup();

    basemapGallery.on("error", function(msg) {
        console.log("basemap gallery error:  ", msg);
    });

    // add search widget
    var searchWidget = new Search({
        map: map,
    }, "divSearch");
    searchWidget.startup();
   
    // run GP task 
    function exportExcel() {
        dlgHide();
        var fs = new FeatureSet();
		
		// get feature set from user choice
		var usrSelect = dom.byId("layer-choice").value;
		
		var exportLayer;
		if (usrSelect == "Fire Hydrants"){
			exportLayer = hydrants;
		}
		else {
			exportLayer = culverts;
		}
		
		// fill in feature set
        fs.features = exportLayer.graphics;
		fs.fields = exportLayer.fields;
		fs.geometryType = exportLayer.geometryType;
	
        // set up params
		var gpParams = {
			"Table": fs, //dojoJSON.toJson(fs, true),
			"Table_Name": usrSelect,
			"Use_Alias_Names": dom.byId("use-alias").checked
		}
		
		var gp = new Geoprocessor("http://lt0212x1g2676:6080/arcgis/rest/services/GP_TASKS/ExportToExcel/GPServer/ExportToExcel");
		
		// because it is synchronous, we use the execute method
		gp.execute(gpParams, gpJobComplete);
                
    };

    // callback for gp job to display pdf
    function gpJobComplete(results, messages) {
		map.graphics.clear();
        var theurl = results[0].value;
        var win = window.open(theurl, "_blank");
        win.focus();
    };

});