$(".multiple-select").chosen();
$( "#event_date" ).datepicker();
$( "#supplement_date" ).datepicker();
$(function() {
    var table = $("table[class=table]");
    $("div[data-toggle=fieldset]").each(function() {
        var $this = $(this);

        //Add new entry
        $this.find("button[data-toggle=fieldset-add-row]").click(function() {
            var target = $($(this).data("target"));
            if (!table.is(":visible")) {
                table.show();
            } else {
                var oldrow = target.find("[data-toggle=fieldset-entry]:last");
                var row = oldrow.clone(true, true);
                var elem_id = row.find(":input")[0].id;
                var elem_num = parseInt(elem_id.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;
                row.attr('data-id', elem_num);
                row.find(":input").each(function() {
                    var id = $(this).attr('id').replace('-' + (elem_num - 1) + '-', '-' + (elem_num) + '-');
                    $(this).attr('name', id).attr('id', id);
                    if ($(this).is(":checkbox")) {
                        $(this).prop('checked', false);
                        $(this).attr({"value": "y"});
                    }
                    if ($(this).is("input:text")) {
                        $(this).val('');
                    }
                });
                oldrow.after(row);
            }
        }); //End add new entry

        //Remove row
        $this.find("button[data-toggle=fieldset-remove-row]").click(function() {
            if($this.find("[data-toggle=fieldset-entry]").length == 1) {
                table.hide();
                var thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                thisRow.find(":input").each(function() {
                    if ($(this).is("select")) {
                        $(this).val(-1);
                    }
                    if ($(this).is("input:text")) {
                        $(this).val('');
                    }
                    if ($(this).is(":checkbox")) {
                        $(this).prop('checked', false);
                        $(this).attr({"value": "y"});
                    }
                });
            }
            if ($this.find("[data-toggle=fieldset-entry]").length > 1) {
                var thisRow = $(this).closest("[data-toggle=fieldset-entry]");
                thisRow.remove();
            }
        }); //End remove row
    });
});

$('.simple-select').chosen({ width: "210px" });
