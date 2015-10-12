from PhonoSearchLib import LangSearchEngine
import json
import csv
import re
import urllib.parse
import time

SEARCH_JS_TEMPLATE = """
    <script>
    function sendQuery(btn) {{
        if (document.getElementById('include_dialects').checked) {{
            var includeDialects = "?dialects=true&";
        }} else {{
            var includeDialects = "?";
        }}
        window.location.assign(window.location.protocol + "//" + window.location.host + window.location.pathname + includeDialects + "query=" + $("#search_field").val())
    }}
    {report_data}
    {add_map}
    </script>
    """

# A piece of JS, which adds a map to the report page
# and populates it with yellow markers corresponding
# to the results of a successful search. It expects 
# the map-holding div to be called "mapCanvas" and 
# the array with the results to be called "reportData".
ADD_MAP = """$(document).ready(function() {
                    var count = 0,
                        meanLat = 0,
                        meanLon = 0;
                    for (var i = 0; i < reportData.length; i++) {
                        count += 1;
                        meanLat += +reportData[i][2];
                    }
                    meanLat = meanLat / count;
                    count = 0;
                    for (var i = 0; i < reportData.length; i++) {
                        count += 1
                        meanLon += +reportData[i][3]
                    }
                    meanLon = meanLon / count;
                    $("#mapCanvas").css({"width": "800px", "height": "500px"});
                    var center = new google.maps.LatLng(meanLat, meanLon);
                    var mapOptions = {
                        zoom: 3,
                        center: center,
                        mapTypeId: google.maps.MapTypeId.TERRAIN
                    }
                    var map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
                    for (var i = 0; i < reportData.length; i++) {
                        var latLng = new google.maps.LatLng(reportData[i][2], reportData[i][3]);
                        var marker = new google.maps.Marker({
                            position: latLng,
                            map: map,
                            title: reportData[i][0] + ", " + reportData[i][5] + ", " + reportData[i][4],
                            icon: {
                                path: google.maps.SymbolPath.CIRCLE,
                                fillColor: "yellow",
                                fillOpacity: 1,
                                scale: 6,
                                strokeWeight: 1,
                                strokeColor: "black"
                            }
                        });
                    }
                });
            """

def get_homepage():
    link = ""
    script = ""
    content = """
    <h3>About</h3>
<p>This site is an interface to the database of Eurasian phonological inventories. The database was conceived and implemented by <a href="https://rggu.academia.edu/DmitryNikolaev" title="">Dmitry Nikolaev</a> (dsnikolaev [at] gmail [dot] com) with contributions from Andrey Nikulin and Anton Kukhto and financial support from <a href="http://ffli.ru" title="Foundation for fundamental studies in linguistics">Foundation for fundamental studies in linguistics</a>. The database includes inventories and additional data for {nvars} language varieties of Eurasia, including {nlangs} languages and {ndials} dialects, with around 150 languages planned for inclusion. The data were gleaned from grammatical descriptions of individual language varieties and reference works on language families. No recycling of existing databases was undertaken.</p>
<h3>How to access the data</h3>
<p>There are three views of the database: <a href="mapview">mapview</a>, <a href="listview">listview</a>, and <a href="segments">segment view</a>. The <a href="mapview">mapview</a> shows all the languages on the map with colours of the points corresponding to families. The entries on the languages can be accessed by clicking on the markers. The <a href="listview">listview</a> shows the languages organised according to their genealogical affiliation and in the alphabetical order. The two-tier description consisting of family (~Indo-European) and group (~Slavic, Germanic) is used. The <a href="segments">segment view</a> presents all the segments that can be found in the languages in the database. The distribution of each segment can be accessed by clicking on it.</p>
<p>The <a href="reports">family/group reports</a> section provides some info on particular families and groups.</p>
<p>There are three ways to query the database. The <a href="search_exact">exact search</a> returns the distribution of individual phonemes and combinations of phonemes (inluding phoneme gaps) in the covered languages. The <a href="search_fuzzy">fuzzy search</a> finds all variants of a base phoneme and their distribution. The <a href="search_feature">feature search</a> finds inventories displaying a particular combination of IPA features (including feature gaps).</p>
<h3>Data dump</h3>
<p>The latest version of the database can be downloaded <a href="http://eurasianphonology.info/static/phono_dbase.json">as a JSON-file</a>.
<h3>Source code</h3>
<p>The database-handling scripts used in this project including IPA parser and tabulator and the source code for this site are <a href="https://github.com/macleginn/eurasian-phonologies">on GitHub</a>.</p>
<h3>Cite</h3>
<p>Nikolaev, Dmitry; Andrey Nikulin; and Anton Kukhto. 2015. The database of Eurasian phonological inventories. (Available online at http://eurasianphonology.info ; accessed on {currentDate})</p>
<p>To cite individual language descriptions, give the source provided in the database record followed by In: Nikolaev, Dmitry; Andrey Nikulin; and Anton Kukhto. 2015. The database of Eurasian phonological inventories. (Available online at http://eurasianphonology.info ; accessed on {currentDate}.)</p>
    """
    nvars  = len(engine_w_dialects.all_langs)
    nlangs = len(engine.all_langs)
    ndials = nvars - nlangs
    currentDate = time.strftime('%B %d, %Y')
    content = content.format(nvars = nvars, nlangs = nlangs, ndials = ndials, currentDate = currentDate)
    data = template.format(link = link, script = script, content = content)
    return data.encode()

def get_mapview(dialects = False):
    family_dic = { key: engine.lang_dic[key]["gen"] for key in engine.lang_dic }
    coords_dic = { key: engine.lang_dic[key]["coords"] for key in engine.lang_dic }
    script = """
    <script>
    var colorNames = ["aquamarine", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell"];
    """ + "var familyDic = " + json.dumps(family_dic, indent = 2, ensure_ascii = False) + ";\n" + \
    "var coordDic = " + json.dumps(coords_dic, indent = 2) + ";\n" + \
    """var addEvent = function(elem, type, eventHandle) {
        if (elem == null || typeof(elem) == 'undefined') return;
        if ( elem.addEventListener ) {
            elem.addEventListener( type, eventHandle, false );
        } else if ( elem.attachEvent ) {
            elem.attachEvent( "on" + type, eventHandle );
        } else {
            elem["on"+type]=eventHandle;
        }
    };
    function resizeMap() {
        var height = $(window).height() - $('#header').height()
        $("#container").css({"height": height});
    }
    addEvent(window, "resize", resizeMap);
    function showMap() {
        $("#container").empty();
        var height = $(window).height() - 115;
        $("#container").css({"height": height});
        var center = new google.maps.LatLng(48, 87.637515);
        var mapOptions = {
                zoom: 3,
                center: center,
                mapTypeId: google.maps.MapTypeId.TERRAIN
            };
        var map = new google.maps.Map(document.getElementById('container'), mapOptions);
        var marker_colors = {
            running_count: 0
        };
        for (var langId in coordDic) {
            var langName = langId.split('#')[0];
            var family = familyDic[langId][0];
            if (!marker_colors.hasOwnProperty(family)) {
                    marker_colors[family] = marker_colors["running_count"];
                    marker_colors["running_count"] += 1;
                }
            var colorIndex = marker_colors[family];
            var latLng = new google.maps.LatLng(coordDic[langId][0], coordDic[langId][1]);
            var marker = new google.maps.Marker({
                position: latLng,
                map: map,
                title: langName + ", " + familyDic[langId][1] + ", " + familyDic[langId][0],
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    fillColor: colorNames[colorIndex],
                    fillOpacity: 1,
                    scale: 6,
                    strokeWeight: 1,
                    strokeColor: "black"
                }
            });
            function makeTableDataFunction(langId) {
                return function() {
                    window.location.assign(window.location.protocol + "//" + window.location.host + "/listview" + "?lang=" + encodeURIComponent(langId))
                }
            }
            google.maps.event.addListener(marker, 'click', makeTableDataFunction(langId));   
        }
    }
    $( document ).ready(function() {
        showMap();
    });
    </script>
    """
    data = template.format(link = """<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>""", script = script, content = "")
    return data.encode()

def get_listview(query):
    content = """<br/>
    <div class="container-fluid">
        <div class="row">
            <div id="threeListsDiv" class="col-xs-3">
                <p>Languages by families and groups:</p>
                <form action="listview" id="langForm">
                <p><select name="family" id="familyList" onchange="repopulateListGroups()" form="langForm">{families}</select></p>
                <p><select name="group" id="groupList" onchange="repopulateListLangs()" form="langForm">{groups}</select></p>
                <p><select name="lang" form="langForm" id="langList">{langs}</select></p>
                <p><input type="submit" class="btn btn-default" value="Show inventory"></p>
                </form>
            </div>
            <div id="alphaListDiv" class="col-xs-3">
                <p>Languages in alphabetical order:</p>
                <form action="listview" id="langForm2">
                <p><select name="lang" form="langForm2" id="alphaList">{langsAlpha}</select></p>
                <p><input type="submit" class="btn btn-default" value="Show inventory"></p>
                </form>
            </div>
        </div>
        {phono_table}
    </div>
    """
    if 'lang' in query:
        phono_table = engine.get_table(query['lang'][0])
    else:
        phono_table = ""

    script = """<script>
    var currentFam   = {current_fam};
    var currentGroup = {current_group};
    var currentLang  = {current_lang};
    var phyloData = {phyloData}
    var groupData = {groupData}"""

    if 'family' in query:
        current_fam   = '"%s"' % query['family'][0];
        current_group = '"%s"' % query['group'][0];
        current_lang  = '"%s"' % query['lang'][0];
    else:
        current_fam = current_group = current_lang = '"default"'

    phyla_dic_list = { key: list(item) for key, item in engine.phyla_dic.items() if item or item == "Isolate"}
    script = script.format(phyloData = json.dumps(phyla_dic_list) + ";\n", groupData = json.dumps(engine.group_dic) + ";\n", current_fam = current_fam, current_group = current_group, current_lang = current_lang)

    script += """
    function repopulateListGroups(familyList) {
        var currentFam = $("#familyList").val();
        console.log(currentFam);
        var groupList  = $("#groupList");
        groupList.empty();
        var group_arr = [];
        phyloData[currentFam].map(function(group) {
            group_arr.push(group);
        });
        group_arr.sort()
        var add_later = false;
        var ungrouped_name;
        for (var i = 0; i < group_arr.length; i++) {
            if (group_arr[i].indexOf("ungrouped", group_arr[i].length - group_arr[i].length) !== -1) {
                add_later = true;
                ungrouped_name = group_arr[i];
            }
            else {
                groupList.append($("<option>").attr("value", group_arr[i]).text(group_arr[i]));
            }
        }
        if (add_later) {
            groupList.append($("<option>").attr("value", ungrouped_name).text("Ungrouped"));
        }
        repopulateListLangs();
    }

    function repopulateListLangs() {
        var currentGroup = $("#groupList").val();
        console.log(currentGroup);
        var langList  = $("#langList");
        langList.empty();
        var langsInGroup = groupData[currentGroup];
        langsInGroup.sort();
        for (var i = 0; i < langsInGroup.length; i++) {
            langList.append($("<option>").attr("value", langsInGroup[i]).text(langsInGroup[i].split("#")[0]));
        }
    }
    </script>
    <script>
    $(document).ready(function() {
        if (currentLang != "default") {
            $("#familyList").val(currentFam);
            repopulateListGroups();
            $("#groupList").val(currentGroup);
            repopulateListLangs();
            $("#langList").val(currentLang);
        }
        });
    </script>"""

    families = []
    sorted_families = [item for item in sorted(engine.phyla_dic)]
    for family in sorted_families:
        families.append('<option value="{value}">{name}</option>'.format(value=family, name=family))
    families = '\n'.join(families)
    first_family = sorted_families[0]

    groups = []
    sorted_groups = sorted(engine.phyla_dic[first_family])
    for group in sorted_groups:
        groups.append('<option value="{value}">{name}</option>'.format(value=group, name=group))
    groups = '\n'.join(groups)
    first_group = sorted_groups[0]

    langs = []
    sorted_langs = sorted(engine.group_dic[first_group])
    for lang in sorted_langs:
        langs.append('<option value="{value}">{name}</option>'.format(value=lang, name=lang.split('#')[0]))
    langs = '\n'.join(langs)

    langs_alpha = []
    all_langs = sorted(engine.all_langs);
    for lang in all_langs:
        langs_alpha.append('<option value="{value}">{name}</option>'.format(value=lang, name=lang.split('#')[0]))
    langs_alpha = '\n'.join(langs_alpha)

    data = template.format(link = "", script = script, content = content.format(families=families, groups = groups, langs = langs, langsAlpha = langs_alpha, phono_table = phono_table))
    return data.encode()

def get_segments():
    script = """
    <script>
    function searchForThis(s) {
        var newUrl = window.location.protocol + "//" + window.location.host + "/search_exact?" + "query=" + s.textContent;
        window.location.assign(newUrl); 
    }
    </script>
    """
    link = """
    <style>
    .hoverRed {
        font-famiy: 'tahoma, times new roman';
    }
    .hoverRed:hover {
        background-color: Beige;
        cursor: pointer;
    }
    </style>
    """
    content = engine_w_dialects.get_full_table()
    data = template.format(link = link, script = script, content = content)
    return data.encode()

def get_reports_page(query, chosen_stock = None):
    link = """<script src="https://maps.googleapis.com/maps/api/js?v=3.exp"></script>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript" charset="utf-8">
        google.load("visualization", "1", {packages:["corechart"]});
    </script>
    <style>
    #main {
        padding-left: 20px;
        padding-right: 20px;
    }
    .chartHolder {
        width:33%;
        float:left;
    }
    </style>
    """
    
    script = """<script>
    var currentFam   = {current_fam};
    var currentGroup = {current_group};
    var phyloData = {phyloData}
    var groupData = {groupData}"""

    if 'group' in query:
        current_fam   = '"%s"' % query['family'][0];
        current_group = '"%s"' % query['group'][0];
    elif 'family' in query:
        current_fam   = '"%s"' % query['family'][0];
        current_group = '"default"'
    else:
        current_fam = current_group = '"default"'

    phyla_dic_list = { key: list(item) for key, item in engine.phyla_dic.items() if item or item == "Isolate" }
    script = script.format(phyloData = json.dumps(phyla_dic_list) + ";\n", groupData = json.dumps(engine.group_dic) + ";\n", current_fam = current_fam, current_group = current_group)

    script += """
    function repopulateGroups(familyList) {
        var currentFam = $("#families").val();
        console.log(currentFam);
        var groupList  = $("#groups");
        groupList.empty();
        var group_arr = [];
        phyloData[currentFam].map(function(group) {
            group_arr.push(group);
        });
        group_arr.sort()
        var add_later = false;
        var ungrouped_name;
        for (var i = 0; i < group_arr.length; i++) {
            if (group_arr[i].indexOf("ungrouped", group_arr[i].length - group_arr[i].length) !== -1) {
                add_later = true;
                ungrouped_name = group_arr[i];
            }
            else {
                groupList.append($("<option>").attr("value", group_arr[i]).text(group_arr[i]));
            }
        }
        if (add_later) {
            groupList.append($("<option>").attr("value", ungrouped_name).text("Ungrouped"));
        }
    }
    function showGroupReport() {
        var newUrl = window.location.protocol + "//" + window.location.host + "/reports?" + "family=" + encodeURI($('#families').val()) + "&group=" + encodeURI($('#groups').val());
        window.location.assign(newUrl); 
    }
    function addInventoryHistogram(table, title) {
        var minVal = +Infinity,
            maxVal = -Infinity;
        for (var i = 1; i < table.length; i++) {
            var val = +table[i][1];
            if (val < minVal) {
                minVal = val;
            }
            if (val > maxVal) {
                maxVal = val;
            }
        }
        var newId = title.replace(" ", "_")
        $("#histogramHolder").append($("<div>").attr("id", newId).attr("class", "chartHolder"))
        var data = google.visualization.arrayToDataTable(table);
        var options = {
            // chartArea: {left: 35, width: 735, top: 35, height: 385},
            width: "100%",
            height: 450,
            colors: ['green'],
            titleTextStyle: {
                fontName: "open sans",
                fontSize: 16
            },
            histogram: {bucketSize: 5},
            title: title,
            legend: {position: "none"},
        };
        var chart = new google.visualization.Histogram(document.getElementById(newId));
        chart.draw(data, options);
    }
    function zip(arr1, arr2) {
        result = [];
        for (var i = 0; i < arr1.length; i++) {
            result.push([arr1[i], arr2[i]]);
        }
        return result
    }
    </script>
    <script>
    $(document).ready(function() {
        if (currentFam != "default") {
            $("#families").val(currentFam);
            repopulateGroups();
        }
        if (currentGroup != "default") {
            $("#groups").val(currentGroup);
        }
        });
    </script>"""

    content = """
    <div id="familiesGroupsLists">
        <h3 id="reportsTitle">Family and groups reports</h3>
        <form id="familyList" action="reports">
            <select id="families" name="family" form="familyList" onchange="repopulateGroups()">{families}</select>
            <input type="submit" value="Show family report">
        </form>
        <form id="groupList" action="reports">
            <select id="groups" name="group" form="groupList">{groups}</select>
            <input type="button" value="Show group report" onclick="showGroupReport()">
        </form>
    </div>
    {report}
    """
    families = []
    sorted_families = [item for item in sorted(engine.phyla_dic)]
    for family in sorted_families:
        families.append('<option value="{value}">{name}</option>'.format(value=family, name=family))
    families = '\n'.join(families)
    first_family = sorted_families[0]

    groups = []
    sorted_groups = sorted(engine.phyla_dic[first_family])
    for group in sorted_groups:
        groups.append('<option value="{value}">{name}</option>'.format(value=group, name=group))
    groups = '\n'.join(groups)

    report = ""

    if current_group != '"default"':
        report_start = """
        <script>
            {data}"""
        report = """
            var mapData = reportData["map_data"];
            var lats = [],
                lons = [];
            mapData.map(function (item) {
                lats.push(+item[1]);
                lons.push(+item[2]);
            });
            var centerLat = lats.reduce(function(a, b) { return a + b }, 0) / lats.length,
                centerLong = lons.reduce(function(a, b) { return a + b }, 0) / lons.length,
                minLat = lats.reduce(function(a, b) {return Math.min(a, b)}),
                minLon = lons.reduce(function(a, b) {return Math.min(a, b)}),
                maxLat = lats.reduce(function(a, b) {return Math.max(a, b)}),
                maxLon = lons.reduce(function(a, b) {return Math.max(a, b)});
            $(document).ready(function() {
                console.log(centerLat);
                console.log(centerLong);
                var center = new google.maps.LatLng(centerLat, centerLong);
                var mapOptions = {
                    zoom: 4,
                    center: center,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };
                var map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
                mapData.map(function(item) {
                    var latLng = new google.maps.LatLng(item[1], item[2]);
                    var marker = new google.maps.Marker({
                        position: latLng,
                        map: map,
                        title: item[0],
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            fillColor: "yellow",
                            fillOpacity: 1,
                            scale: 6,
                            strokeWeight: 1,
                            strokeColor: "black"
                        }
                    });
                });
                if (reportData["inv_sizes"]["all"].length > 1) {
                    $("#reportHolder").append("<br />")
                    $("#reportHolder").append($("<div>").attr("id", "histogramHolder"));
                    $("#histogramHolder").append($("<h3>").attr("class", "main_div_title").text("Inventory size breakdown"));
                    var table = [["Language", "Inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["all"]));
                    addInventoryHistogram(table, "Inventory sizes: all segments");
                    table = [["Language", "Consonant inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["cons"]));
                    addInventoryHistogram(table, "Inventory sizes: consonants");
                    table = [["Language", "Vowel inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["vows"]));
                    addInventoryHistogram(table, "Inventory sizes: vowels");
                }
            });         
        </script>"""
        report_div = """
        <div id="reportHolder">
            <div id="mapCanvas" style="width: 600px; height: 375px; margin-top: 20px;"></div>
            {phono_table}
        </div>
        """
        langs_to_report = engine.group_dic[query['group'][0]]
        report_dic = {}
        report_dic["map_data"] = []
        for lang in langs_to_report:
            report_dic["map_data"].append(
                [lang.split('#')[0],
                engine.lang_dic[lang]["coords"][0],
                engine.lang_dic[lang]["coords"][1]]
                )
        report_dic["inv_sizes"] = engine.get_inv_sizes(langs_to_report)
        data = "var reportData = " + json.dumps(report_dic, indent = 2) + ";\n"
        phono_table = engine.get_common_table(langs_to_report)
        report = report_start.format(data = data) + report + report_div.format(data = data, phono_table = phono_table)

    elif current_fam != '"default"':
        report_start = """
        <script>
            {data}"""
        report = """
            var colorNames = ["aquamarine", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell"];
            var mapData = reportData["map_data"];
            var lats = [],
                lons = [];
            mapData.map(function (item) {
                lats.push(+item[2]);
                lons.push(+item[3]);
            });
            var centerLat = lats.reduce(function(a, b) { return a + b }, 0) / lats.length,
                centerLong = lons.reduce(function(a, b) { return a + b }, 0) / lons.length,
                minLat = lats.reduce(function(a, b) {return Math.min(a, b)}),
                minLon = lons.reduce(function(a, b) {return Math.min(a, b)}),
                maxLat = lats.reduce(function(a, b) {return Math.max(a, b)}),
                maxLon = lons.reduce(function(a, b) {return Math.max(a, b)});
            $(document).ready(function() {
                console.log(centerLat);
                console.log(centerLong);
                var center = new google.maps.LatLng(centerLat, centerLong);
                var mapOptions = {
                    zoom: 3,
                    center: center,
                    mapTypeId: google.maps.MapTypeId.TERRAIN
                };
                var map = new google.maps.Map(document.getElementById('mapCanvas'), mapOptions);
                var marker_colors = {
                    running_count: 0
                };
                mapData.map(function(item) {
                    if (!marker_colors.hasOwnProperty(item[1])) {
                        marker_colors[item[1]] = marker_colors["running_count"];
                        marker_colors["running_count"] += 1;
                    }
                    var colorIndex = marker_colors[item[1]];
                    var latLng = new google.maps.LatLng(item[2], item[3]);
                    var marker = new google.maps.Marker({
                        position: latLng,
                        map: map,
                        title: item[0],
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            fillColor: colorNames[colorIndex],
                            fillOpacity: 1,
                            scale: 6,
                            strokeWeight: 1,
                            strokeColor: "black"
                        }
                    })
                });
                if (reportData["inv_sizes"]["all"].length > 1) {
                    $("#reportHolder").append("<br />")
                    $("#reportHolder").append($("<div>").attr("id", "histogramHolder"));
                    $("#histogramHolder").append($("<h3>").attr("class", "main_div_title").text("Inventory size breakdown"));
                    var table = [["Language", "Inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["all"]));
                    addInventoryHistogram(table, "Inventory sizes: all segments");
                    table = [["Language", "Consonant inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["cons"]));
                    addInventoryHistogram(table, "Inventory sizes: consonants");
                    table = [["Language", "Vowel inventory size"]];
                    table.push.apply(table, zip(mapData.map(function(item) {return item[0]}), reportData["inv_sizes"]["vows"]));
                    addInventoryHistogram(table, "Inventory sizes: vowels");
                }
            });         
        </script>"""
        report_div = """
        <div id="reportHolder">
            <div id="mapCanvas" style="width: 600px; height: 375px; margin-top: 20px;"></div>
            {phono_table}
        </div>
        """
        langs_to_report = engine.family_dic[query['family'][0]]
        report_dic = {}
        report_dic["map_data"] = []
        for lang in langs_to_report:
            report_dic["map_data"].append(
                [lang.split('#')[0],
                engine.lang_dic[lang]["gen"][1],
                engine.lang_dic[lang]["coords"][0],
                engine.lang_dic[lang]["coords"][1]]
                )
        report_dic["inv_sizes"] = engine.get_inv_sizes(langs_to_report)
        data = "var reportData = " + json.dumps(report_dic, indent = 2) + ";\n"
        phono_table = engine.get_common_table(langs_to_report)
        report = report_start.format(data = data) + report + report_div.format(data = data, phono_table = phono_table)
    else:
        print("Lists only")

    data = template.format(link = link, script = script, content = content.format(families = families, groups = groups, report = report))
    return data.encode()

def format_table(table, css_class = ""):
    if len(table) > 1:
        header = str(len(table)) + " languages:"
    else:
        header = "One language:"
    result = """<h4 style="margin-top: 20px;">%s</h4><table{css_class}>
{rows}</table>""" % header
    rows_arr = []
    for row in table:
        new_row = []
        for el in row:
            new_row.append("\t\t<td>%s</td>\n" % el)
        new_row = """\t<tr>
{row}\t</tr>\n""".format(row = ''.join(new_row))
        rows_arr.append(new_row)
    return result.format(css_class = ' class="%s"' % css_class, rows = ''.join(rows_arr))

def search(search_type, query):
    if search_type == 'exact':
        phono_list = re.split(r'\s*,\s*', query['query'][0])
        phono_string = ', '.join(phono_list)
        if 'dialects' in query:
            result = sorted(engine_w_dialects.IPA_query_multiple(*phono_list))
        else:
            result = sorted(engine.IPA_query_multiple(*phono_list))
        table = []
        for lang in result:
            table.append([
                    lang_dic[lang]["name"], lang_dic[lang]["code"], lang_dic[lang]["coords"][0], lang_dic[lang]["coords"][1], lang_dic[lang]["gen"][0], lang_dic[lang]["gen"][1]
                ])
        return table
    elif search_type == 'superset':
        if 'dialects' in query:
            try:
                result = engine_w_dialects.IPA_query(query['query'][0]) # A dictionary
            except:
                result = {}
        else:
            try:
                result = engine.IPA_query(query['query'][0])
            except:
                result = {}
        result_dic = {}
        for key in result:
            result_dic[key] = []
            for lang in result[key]:
                result_dic[key].append([
                    lang_dic[lang]["name"], lang_dic[lang]["code"], lang_dic[lang]["coords"][0], lang_dic[lang]["coords"][1], lang_dic[lang]["gen"][0], lang_dic[lang]["gen"][1]
                ])
        return result_dic
    elif search_type == 'feature':
        feature_list = re.split(r'\s*,\s*', query['query'][0])
        if 'dialects' in query:
            result = sorted(engine_w_dialects.features_query(*feature_list))
        else:
            result = sorted(engine.features_query(*feature_list))
        table = []
        for lang in result:
            table.append([
                    lang_dic[lang]["name"], lang_dic[lang]["code"], lang_dic[lang]["coords"][0], lang_dic[lang]["coords"][1], lang_dic[lang]["gen"][0], lang_dic[lang]["gen"][1]
                ])
        return table
    else:
        return None

def get_exact_search(query = None):
    # DESCRIBE MULTIPLE SEARCH!!!
    link = """<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>"""
    script = SEARCH_JS_TEMPLATE
    content = """<div id="main">
    <div id="searchFields">
    <label for="include_dialects">Include dialects: </label>
    <input id="include_dialects" type="checkbox">
    <br/>
    <label class="search_label" for="search_field">Exact phoneme search: </label>
    <input id="search_field" type="text">
    <input onclick="sendQuery(this)" value="Submit" id="exact_search_btn" type="button">
    <p class="info">Input a single phoneme or a list of comma-separated phonemes encoded by IPA symbols. Some or all of the phonemes can be preceded by a ‘-’ symbol. A list of inventories having all the phonemes without ‘-’ and lacking all the phonemes with ‘-’ will be returned. An example search: <span class="phono">‘a, -b, cʰ, -dʲ’</phono>. Online tools such as <a href="http://ipa.typeit.org/full/" target="_blank">Type IPA</a> can be used for typing convenience.</p>
    </div>
  <div id="mapCanvas"></div>
  <div id="reportCanvas">{response}</div>
</div>"""
    if not query:
        response = report_data = add_map = ""
    else:
        try:
            results = search("exact", query)
            if results:
                response = format_table(results, "search_results")
                report_data = "var reportData = " + json.dumps(results, indent = 2, ensure_ascii = False) + ';\n'
                add_map = ADD_MAP
            else:
                response = "The phoneme or combination of phonemes was not found."
                report_data = add_map = ""
        except:
            response = "<strong>Malformed request!</strong>"
            report_data = add_map = ""
    script = script.format(report_data = report_data, add_map = add_map)
    content = content.format(response = response)
    data = template.format(link = link, script = script, content = content)
    return data.encode()

def get_fuzzy_search(query = None):
    link = """<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>"""
    script = SEARCH_JS_TEMPLATE
    content = """<div id="main">
    <div id="searchFields">
    <label for="include_dialects">Include dialects: </label>
    <input id="include_dialects" type="checkbox">
    <br/>
    <label class="search_label" for="search_field">Fuzzy phoneme search: </label>
    <input id="search_field" type="text">
    <input onclick="sendQuery(this)" value="Submit" id="superset_search_btn" type="button">
    <p class="info">Input a base phoneme in terms of IPA symbols. The search engine will provide all phonemes from the database which include all the features of the base phoneme along with their distributions. An example search: ‘p’.</p>
    <div id="reportCanvas">{response}</div>
</div>"""
    if not query:
        response = report_data = add_map = ""
    else:
        results = search('superset', query)
        if not results:
            response = "Nothing found."
            report_data = add_map = ""
        else:
            response = ""
            report_data = "\tvar query = \"" + query['query'][0] + "\";\n\tvar reportData = " + json.dumps(results, indent = 2, ensure_ascii = False) + ';\n'
            add_map = """
            function addSubreport(count, phoneme, langTable) {
                var p = $("<p>")
                if (langTable.length > 1) {
                    var langs = " languages: ";
                } else {
                    var langs = " language: ";
                }
                p.append($("<b>").html("<span class='phono'>" + phoneme + "</span>, " + langTable.length + langs))
                var langList = [];
                for (var i = 0; i < langTable.length; i++) {
                    langList.push(langTable[i][0]);
                }
                p.append(langList.join(', '));
                $("#reportCanvas").append(p);
                var mapCanvasId = "map_canvas_" + count;
                $("#reportCanvas").append($("<div>").attr("id", mapCanvasId).css({"width": "600px", "height": "375px", "margin-top": "20px", "margin-bottom": "20px", "background-color": "beige"}))
                var center = new google.maps.LatLng(48, 87.637515);
                var mapOptions = {
                        zoom: 2,
                        center: center,
                        mapTypeId: google.maps.MapTypeId.TERRAIN
                    };
                var map = new google.maps.Map(document.getElementById(mapCanvasId), mapOptions);
                for (var i = 0; i < langTable.length; i++) {
                    langList.push(langTable[i][0]);
                    var latLng = new google.maps.LatLng(langTable[i][2], langTable[i][3]);
                    var marker = new google.maps.Marker({
                        position: latLng,
                        map: map,
                        title: langTable[i][0] + ", " + langTable[i][5] + ", " + langTable[i][4],
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            fillColor: "yellow",
                            fillOpacity: 1,
                            scale: 6,
                            strokeWeight: 1,
                            strokeColor: "black"
                        }
                    });
                }
            }
            $(document).ready(function () {
                var keys = [];
                for (var key in reportData) {
                    if (reportData.hasOwnProperty(key)) {
                        keys.push(key);
                    }
                }
                if (keys.length == 0) {
                    $("#reportCanvas").append($("<h4>").html("The base phoneme /<span class='phono'>" + query + "/</span> was not found"));      
                } else {
                    if (keys.length == 1) {
                        var vars = " variant:";
                    }
                    else {
                        var vars = " variants:";
                    }
                    $("#reportCanvas").append($("<h4>").html("The base phoneme /<span class='phono'>" + query + "/</span> has " + keys.length + vars));
                    keys.sort();
                    for (var i = 0; i < keys.length; i++) {
                        addSubreport(i, keys[i], reportData[keys[i]]);
                    }
                }
                });
            """
    content = content.format(response = response)
    script = script.format(report_data = report_data, add_map = add_map)
    data = template.format(link = link, script = script, content = content)
    return data.encode()

def get_feature_search(query = None):
    link = """<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>"""
    script = SEARCH_JS_TEMPLATE
    content = """<div id="main">
    <div id="searchFields">
    <label for="include_dialects">Include dialects: </label>
    <input id="include_dialects" type="checkbox">
    <br/>
    <label class="search_label" for="search_field">Feature search: </label>
    <input id="search_field" type="text"><input onclick="sendQuery(this)" value="Submit" id="feature_search_btn" type="button">
    <p class="info">Input a list of comma-separated IPA features. Some or all of the features can be preceded by a ‘-’ symbol. A list of inventories having segments exhibiting all the features without ‘-’ and lacking all the features with ‘-’ will be returned. Features can be simple (‘plosive’, ‘glottalised’, 'triphthong') or composite (‘voiceless fricative’, ‘retroflex tap’). An example search: ‘voiced lateral fricative, -lateral affricate’.
    <br>
    The following features are supported: <em>advanced, advanced-tongue-root, affricate, affricated, alveolar, alveolo-palatal, apical, approximant, aspirated, back, bilabial, breathy-voiced, central, centralised, close, close-mid, creaky-voiced, dental, diphthong, epiglottal, faucalised, fricative, front, glottal, glottalised, half-long, hissing-hushing, implosive, labial-palatal, labial-velar, labialised, labiodental, lateral, lateral-released, less-rounded, long, lowered, mid, mid-centralised, more-rounded, nasal, nasalised, near-back, near-close, near-front, near-open, non-syllabic, open, open-mid, palatal, palatal-velar, palatalised, pharyngeal, pharyngealised, plosive, postalveolar, pre-aspirated, pre-glottalised, pre-labialised, pre-nasalised, raised, retracted, retracted-tongue-root, retroflex, rhotic, rounded, syllabic, tap, trill, triphthong, ultra-short, unreleased, unrounded, uvular, velar, velarised, voiced, voiceless, weakly-articulated</em>.</p>
    <div id="mapCanvas"></div>
    <div id="reportCanvas">{response}</div>
</div>"""
    if not query:
        response = report_data = add_map = ""
    else:
        results = search("feature", query)
        if results:
            response = format_table(results, "search_results")
            report_data = "var reportData = " + json.dumps(results, indent = 2, ensure_ascii = False) + ';\n'
            add_map = ADD_MAP
        else:
            response = report_data = add_map = ""
    script = script.format(report_data = report_data, add_map = add_map)
    content = content.format(response = response)
    data = template.format(link = link, script = script, content = content)
    return data.encode()

def app(environ, start_response):
    url = urllib.parse.urlsplit(environ['RAW_URI'])
    query = urllib.parse.parse_qs(url.query)
    path = url.path.split('/')[1:]
    print(path)
    print(query.encode('unicode_escape'))
    if not path[0]:
        status = '200 OK'
        data = get_homepage()
    elif path[0] == 'mapview':
        status = '200 OK'
        data = get_mapview()
    elif path[0] == 'listview':
        status = '200 OK'
        data = get_listview(query)
    elif path[0] == 'segments':
        status = '200 OK'
        data = get_segments()
    elif path[0] == 'reports':
        status = '200 OK'
        data = get_reports_page(query)
    elif path[0] == 'search_exact':
        status = '200 OK'
        data = get_exact_search(query)
    elif path[0] == 'search_fuzzy':
        status = '200 OK'
        data = get_fuzzy_search(query)
    elif path[0] == 'search_feature':
        status = '200 OK'
        data = get_feature_search(query)
    elif path[0] == 'get_data':
        status = '200 OK'
        data = str(path).encode() + str(query).encode()
    else:
        status = '404 Not Found'
        data = status.encode()
    response_headers = [
        ('Content-type','text/html'),
        ('Content-Length', str(len(data)))
    ]
    start_response(status, response_headers)
    return iter([data])

engine            = LangSearchEngine('dbase/phono_dbase.json', False)
engine_w_dialects = LangSearchEngine('dbase/phono_dbase.json', True)
with open('dbase/phono_dbase.json', 'r', encoding = 'utf-8') as inp:
    lang_dic = json.load(inp)

with open('../html/template.html', 'r', encoding = 'utf-8') as inp:
    template = inp.read()
