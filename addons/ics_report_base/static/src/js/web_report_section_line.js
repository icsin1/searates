/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";

const { Component, useState } = owl;


export class WebReportSectionLine extends Component {

    static template = 'WebReportSectionLineContainer'

    setup() {
        super.setup(...arguments);
        this.rpc = useService("rpc");
        this.state = useState({});
    }

    constructor(parent, props){
        super(parent, props);
        this.sections = this.props.lines;
        this.parent = this.props.parent;
        this.headers = _.keys(this.props.values);
    }
}
