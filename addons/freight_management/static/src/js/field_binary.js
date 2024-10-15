
odoo.define('freight_management.drag_and_drop_widget', function (require) {
    "use strict"

    var fieldRegistry = require('web.field_registry')
    var FieldBinaryFile = require('web.basic_fields').FieldBinaryFile

    var FieldBinaryFileDragAndDrop = FieldBinaryFile.extend({
        start: function () {
            this._super.apply(this, arguments)
            this.$el.on("drop", this.proxy("_onDropDown"))
            this.$el.on("dragenter", this.proxy("_disableDefaultDragEvents"))
            this.$el.on("dragover", this.proxy("_disableDefaultDragEvents"))
            this.$el.on("dragleave", this.proxy("_disableDefaultDragEvents"))
        },

        _onDropDown: function (e) {
            e.preventDefault()
            e.stopPropagation()

            const _$inputFile = this.$('.o_input_file')

            if (_$inputFile.length === 0) return

            const dataTransfer = e.originalEvent.dataTransfer

            if (dataTransfer.files.length > 1) {
                console.warn("Allowed only one file to upload")
            }
            else {
                _$inputFile[0].files = dataTransfer.files
                _$inputFile.trigger("change")
            }
        },

        _disableDefaultDragEvents: function (e) {
            e.preventDefault()
        },
    })

    fieldRegistry.add('drag_and_drop', FieldBinaryFileDragAndDrop)

    return {
        FieldBinaryFileDragAndDrop: FieldBinaryFileDragAndDrop,
    }
})