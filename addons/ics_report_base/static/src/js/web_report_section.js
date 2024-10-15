/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";

const { Component, useState } = owl;
// const { useRef } = owl.hooks;


export class WebReportSection extends Component {

    static template = 'WebReportSection'

    setup() {
        super.setup(...arguments);
        this.rpc = useService("rpc");
        this.state = useState({});
    }

    constructor(parent, props){
        super(parent, props);
        this.data = props.data;
        this.sections = this.data.sections;
        this.attributes = this.data.attrs;
        this.headers = this.data.options.headers;
        this.group_headers = this.data.options.report_header_groups;
        this.options = this.data.options;
    }
}
