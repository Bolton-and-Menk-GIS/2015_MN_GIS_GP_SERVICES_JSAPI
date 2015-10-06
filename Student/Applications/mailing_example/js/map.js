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
    "esri/dijit/Search",
    "esri/InfoTemplate",
    "esri/dijit/Popup",
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
    Search,
    InfoTemplate,
    Popup,
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
    map.addLayer(bell);

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
    on(dom.byId("gpOK"), "click", initDrawTool);

    function dlgHide() {
        var whitebg = dom.byId("white-background");
        var dlg = dom.byId("dlgbox");
        whitebg.style.display = "none";
        dlg.style.display = "none";
    }

    function showDialog() {
        var whitebg = dom.byId("white-background");
        var dlg = dom.byId("dlgbox");
        whitebg.style.display = "block";
        dlg.style.display = "block";
        var winWidth = window.innerWidth;
        dlg.style.left = (winWidth / 2) - 480 / 2 + "px";
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

    // feature set for selected parcels
    var parcelLayerUrl = "http://lt0212x1g2676:6080/arcgis/rest/services/BELL/Bell_Webmap_REST/MapServer/6";
    parSelection = new FeatureSet();

    // add search widget
    var searchWidget = new Search({
        map: map,
    }, "divSearch");
    searchWidget.startup();

    // Wire draw polygon button to initiate drawing
    on(dom.byId("btnDraw"), "click", initDrawTool);
    on(dom.byId("executeButton"), "click", generateMailingLabels);

    function initDrawTool() {

        // Implement the Draw toolbar
        dlgHide();
        var tbDraw = new Draw(map);
        tbDraw.on("draw-end", function displayPolygon(evt) {

            // Get the geometry from the event object
            geometryInput = evt.geometry;

            // Define symbol for finished polygon
            var tbDrawSymbol = new SimpleFillSymbol(SimpleFillSymbol.STYLE_SOLID, new SimpleLineSymbol(SimpleLineSymbol.STYLE_DASHDOT, new Color([255, 255, 0]), 2), new Color([255, 255, 0, 0.2]));

            // Clear the map's graphics layer
            map.graphics.clear();

            // Construct and add the polygon graphic
            var graphicPolygon = new Graphic(geometryInput, tbDrawSymbol);
            map.graphics.add(graphicPolygon);
            tbDraw.deactivate();

            // generate mailing labels
            generateMailingLabels();

        });
        tbDraw.activate(Draw.EXTENT);
    };

    // run GP task 
    function generateMailingLabels() {
        var features = [];
        features.push(new Graphic(geometryInput));
        var fs = new FeatureSet();
        fs.features = features;

        // build a feature set with an esriRequest (note: could also use queryTask)
        var e = geometryInput.getExtent();
        var parcelRequest = esriRequest({
            url: parcelLayerUrl + "/query",
            content: {
                geometry: e.xmin + "," + e.ymin + "," + e.xmax + "," + e.ymax,
                geometryType: "esriGeometryEnvelope",
                inSR: geometryInput.spatialReference.wkid,
                f: "json",
                outFields: "*"
            },
            handleAs: "json"
        });

        parcelRequest.then(function(response) {

                var gpParams = {
                    "Boundary": dojoJSON.toJson(response, true),
                    "Site": "BellePlaine",
                    "Mailing_Type": dom.byId("mailing").value
                }

                var gp = new Geoprocessor("http://lt0212x1g2676:6080/arcgis/rest/services/GP_TASKS/MailingLabels_Sample/GPServer/MailingLabels");

                // because it is synchronous, we use the execute method
                gp.execute(gpParams, gpJobComplete);
            }),
            function(error) {
                alert(dojoJSON.toJson(error, true))
            };
    };

    // callback for gp job to display pdf
    function gpJobComplete(results, messages) {
        map.graphics.clear();
        var theurl = results[0].value;
        var win = window.open(theurl, "_blank");
        win.focus();
    };

});