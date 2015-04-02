var postback = ''

var set_postback_host = function(pb) {
	postback = pb;
}

// create our editable grid
//
var editableGrid = new EditableGrid("JobGrid", {
		enableSort: true, // true is the default, set it to false if you don't want sorting to be enabled
		editmode: "absolute", // change this to "fixed" to test out editorzone, and to "static" to get the old-school mode
		editorzoneid: "edition", // will be used only if editmode is set to "fixed"
		pageSize: 10
	});


// PROGRESS BAR
/**
 * Progressbar cell renderer
 * @constructor
 * @class Class to render a cell with an HTML progressbar
 */

window.onload = function() {

/*
	editableGrid = new EditableGrid("JobGrid", {
		enableSort: true, // true is the default, set it to false if you don't want sorting to be enabled
		editmode: "absolute", // change this to "fixed" to test out editorzone, and to "static" to get the old-school mode
		editorzoneid: "edition", // will be used only if editmode is set to "fixed"
		pageSize: 10,
		maxBars: 10
	});*/

	editableGrid.onloadJSON(postback + "/jobs/listex");
	setRefreshTimeout();
}

// refresh
var refreshInterval = 5;
var refreshTimeout = undefined;
function setRefreshTimeout()
{
	refreshTimeout = setTimeout(
						function() {
	      					editableGrid.onloadJSON(postback + "/jobs/listex");
	      					setRefreshTimeout();
						}, refreshInterval * 1000);
}

// helper function to display a message
function displayMessage(text, style) {
	_$("message").innerHTML = "<p class='" + (style || "ok") + "'>" + text + "</p>";
}

// helper function to get path of an image
function image(relativePath) {
	return "images/" + relativePath;
}

// this will be used to render our table headers
function InfoHeaderRenderer(message) {
	this.message = message;
	this.infoImage = new Image();
	this.infoImage.src = image("information.png");
};



// this function will initialize our editable grid
EditableGrid.prototype.initializeGrid = function()
{
	with (this) {

		// register the function that will handle model changes
		modelChanged = function(rowIndex, columnIndex, oldValue, newValue, row) {
			// displayMessage("Value for '" + this.getColumnName(columnIndex) + "' in row " + this.getRowId(rowIndex) + " has changed from '" + oldValue + "' to '" + newValue + "'");
   	    	// this.renderCharts();
		};

		// update paginator whenever the table is rendered (after a sort, filter, page change, etc.)
		tableRendered = function() { this.updatePaginator(); };

		// update charts when the table is sorted or filtered
		// tableFiltered = function() { this.renderCharts(); };
		// tableSorted = function() { this.renderCharts(); };

		rowSelected = function(oldRowIndex, newRowIndex) {
			// if (oldRowIndex < 0) displayMessage("Selected row '" + this.getRowId(newRowIndex) + "'");
			// else displayMessage("Selected row has changed from '" + this.getRowId(oldRowIndex) + "' to '" + this.getRowId(newRowIndex) + "'");
		};

		rowRemoved = function(oldRowIndex, rowId) {
			// displayMessage("Removed row '" + oldRowIndex + "' - ID = " + rowId);
		};

		// use a progressbar to render the progress
		setCellRenderer("progress", new CellRenderer({
			render: function(cell, value) { cell.innerHTML = "<progress value='" + value + "' max='100'/>"; }
		}));


		// render the grid (parameters will be ignored if we have attached to an existing HTML table)
		renderGrid("tablecontent", "jobgrid", "tableid");

		// set active (stored) filter if any
		_$('filter').value = currentFilter ? currentFilter : '';

		// filter when something is typed into filter
		_$('filter').onkeyup = function() { editableGrid.filter(_$('filter').value); };

		// bind page size selector
		$("#pagesize").val(pageSize).change(function() { editableGrid.setPageSize($("#pagesize").val()); });
		$("#refresh").val(refreshInterval).change(function() {

			if ( refreshTimeout != undefined ) {
				clearTimeout(refreshTimeout);
			}

			setRefreshTimeout();
		});
	}
};

EditableGrid.prototype.onloadJSON = function(url)
{
	// register the function that will be called when the JSON has been fully loaded
	this.tableLoaded = function() {
		displayMessage("Grid loaded from JSON: " + this.getRowCount() + " row(s)");
		this.initializeGrid();
	};

	console.log('loading job list from ' + url);
	// load JSON URL
	this.loadJSON(url);
};

EditableGrid.prototype.onloadHTML = function(tableId)
{
	// metadata are built in Javascript: we give for each column a name and a type
	this.load({ metadata: [
	    { name: "jobid", datatype: "string", editable: true },
	]});

	// we attach our grid to an existing table
	this.attachToHTMLTable(_$(tableId));
	// displayMessage("Grid attached to HTML table: " + this.getRowCount() + " row(s)");

	this.initializeGrid();
};

// function to render our two demo charts
EditableGrid.prototype.renderCharts = function()
{
	// this.renderBarChart("barchartcontent", 'Age per person' + (this.getRowCount() <= this.maxBars ? '' : ' (first ' + this.maxBars + ' rows out of ' + this.getRowCount() + ')'), 'name', { limit: this.maxBars, bar3d: false, rotateXLabels: this.maxBars > 10 ? 270 : 0 });
	// this.renderPieChart("piechartcontent", 'Country distribution', 'country', 'country');
};

// function to render the paginator control
EditableGrid.prototype.updatePaginator = function()
{
	var paginator = $("#paginator").empty();
	var nbPages = this.getPageCount();

	// get interval
	var interval = this.getSlidingPageInterval(20);
	if (interval == null) return;

	// get pages in interval (with links except for the current page)
	var pages = this.getPagesInInterval(interval, function(pageIndex, isCurrent) {
		if (isCurrent) return "" + (pageIndex + 1);
		return $("<a>").css("cursor", "pointer").html(pageIndex + 1).click(function(event) { editableGrid.setPageIndex(parseInt($(this).html()) - 1); });
	});

	// "first" link
	var link = $("<a>").html("<img src='" + image("gofirst.png") + "'/>&nbsp;");
	if (!this.canGoBack()) link.css({ opacity : 0.4, filter: "alpha(opacity=40)" });
	else link.css("cursor", "pointer").click(function(event) { editableGrid.firstPage(); });
	paginator.append(link);

	// "prev" link
	link = $("<a>").html("<img src='" + image("prev.png") + "'/>&nbsp;");
	if (!this.canGoBack()) link.css({ opacity : 0.4, filter: "alpha(opacity=40)" });
	else link.css("cursor", "pointer").click(function(event) { editableGrid.prevPage(); });
	paginator.append(link);

	// pages
	for (p = 0; p < pages.length; p++) paginator.append(pages[p]).append(" | ");

	// "next" link
	link = $("<a>").html("<img src='" + image("next.png") + "'/>&nbsp;");
	if (!this.canGoForward()) link.css({ opacity : 0.4, filter: "alpha(opacity=40)" });
	else link.css("cursor", "pointer").click(function(event) { editableGrid.nextPage(); });
	paginator.append(link);

	// "last" link
	link = $("<a>").html("<img src='" + image("golast.png") + "'/>&nbsp;");
	if (!this.canGoForward()) link.css({ opacity : 0.4, filter: "alpha(opacity=40)" });
	else link.css("cursor", "pointer").click(function(event) { editableGrid.lastPage(); });
	paginator.append(link);
};

var add_job = function(manga_url, ch_from, ch_to, vol, frm, prf) {
	console.log('add manga: ' + manga_url);

	if (ch_from == '')
		ch_from = -1
	if (ch_to == '')
		ch_to = -1
	if (vol == '')
		vol = -1


	var json = {"url": manga_url, "from": ch_from, "to": ch_to,
                "volume": vol, "format": frm, "profile": prf};

	var xmlhttp;
	if (window.XMLHttpRequest)
	{ // code for IE7+, Firefox, Chrome, Opera, Safari
		xmlhttp = new XMLHttpRequest();
	}
	else
	{ // code for IE6, IE5
		xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
	}

	xmlhttp.onreadystatechange=function()
	{
		if (xmlhttp.readyState==4 && xmlhttp.status==200)
	    {
	    	console.log('job added');
	    	// document.getElementById("myDiv").innerHTML=xmlhttp.responseText;
	    }
    }

    var body = "body=" + encodeURIComponent(JSON.stringify(json));

	xmlhttp.open("POST", postback + "/jobs/add" ,true);

	xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

	xmlhttp.send(body);
}

