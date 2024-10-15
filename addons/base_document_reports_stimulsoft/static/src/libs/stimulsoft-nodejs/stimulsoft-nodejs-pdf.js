/*
    THIS FILE IS CREATED TO GENERATE STIMULSOFT REPORT BY NODEJS BACKEND

    it required arguments to be passed when calling by command line
    args = [template_id, record_id, base_url, session_id]

    These arguments are used to call api for reading template data and record json data
    with stimulsoft viewer license key

    as a result of generated pdf, it logging as text which will be picked by python script as
    generated pdf file
*/

var tiny = require('tiny-json-http')
var Stimulsoft = require('stimulsoft-reports-js');

var args = process.argv;
var session_id = args.pop();

const headers = {
    'Content-Type': 'application/json',
    'Cookie': 'session_id=' + session_id
}

const data = {
    'params': {
        'record_id': args.pop(),
        'template_id': args.pop()
    }
}
const url = 'http://0.0.0.0:8069/stimulsoft-nodejs/get-data';

tiny.post({ url, data, headers }, function (error, result) {
    if (result) {
        var response = result.body.result;
        processDocument(response.gc_si_key, response.template, response.record);
    } else if (error) {
        console.log("ERROR: " + JSON.stringify(error));
    }
});

function processDocument(gc_si_key, template_data, json_data) {
    // Setting license key
    Stimulsoft.Base.StiLicense.key = gc_si_key;

    var report = new Stimulsoft.Report.StiReport();

    // Loading report template
    report.load(template_data);

    // Setting report data
    var dataSet = new Stimulsoft.System.Data.DataSet("root");
    dataSet.readJson(json_data);
    report.regData("root", "root", dataSet);

    report.renderAsync(() => {
      report.exportDocumentAsync((pdfData) => {
          var buffer = Buffer.from(pdfData)
          console.log(buffer.toString('base64'));
      }, Stimulsoft.Report.StiExportFormat.Pdf);
    });
}
