$(function () {

    $(document).ready(function() {
        let alert_msg_div = $('#alert-message');
        if(alert_msg_div.length)  {
            alert_msg_div.focus();
        }
        $(".diff-select").each(function() {
            if ($(this).val() === "No, I failed to complete the task") {
                let select_id = $(this).attr("id");
                let task_no = select_id.substring(select_id.lastIndexOf("-") + 1);
                let diag_type = $('#diagram-type').val();
                if (task_no && diag_type === 'Dialogue System') {
                    let reason_div_id = "#fail-reason-task-" + task_no + "-container";
                    let feedback_div_id = "#fail-feedback-task-" + task_no + "-container";
                    $(reason_div_id).show();
                    let reason_select_id = '#fail-reason-task-' + task_no;
                    if ($(reason_select_id).val() === "Other reason") {
                        $(feedback_div_id).show();
                    }
                }
            }
        });
    });

    $('#navtabs a').on("click", function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    $('#inputRetrieve').on("keypress", function(e) {
        if (e.which === 13) {
            $("#submit-retrieve").click();
        }
    });

    $('#permissions-all').on("click", function (e) {
        let checkboxes = $('#table-permissions div.checkbox input[type=checkbox]');
        for (let i=0; i<checkboxes.length; i++) {
            checkboxes[i].checked = true;
        }
    });

    $('#permissions-none').on("click", function (e) {
        let checkboxes = $('#table-permissions div.checkbox input[type=checkbox]');
        for (let i=0; i<checkboxes.length; i++) {
            checkboxes[i].checked = false;
        }
    });

    $("#sight").on("change", function() {
        if (this.value !== "I am totally blind" &&
            this.value !== "I have near total blindness") {
            $('#blind-length-container').hide();
        } else {
            $('#blind-length-container').show();
        }
    });

    function handle_task_change(select_elem) {
        let select_id = select_elem.attr("id");
        let task_no = select_id.substring(select_id.lastIndexOf("-") + 1);
        if (task_no) {
            let reason_div_id = "#fail-reason-task-" + task_no + "-container";
            let feedback_div_id = "#fail-feedback-task-" + task_no + "-container";
            let diag_type = $('#diagram-type').val();
            if (select_elem.val() === "No, I failed to complete the task" && diag_type === 'Dialogue System') {
                $(reason_div_id).show();
                let reason_select_id = '#fail-reason-task-' + task_no;
                if ($(reason_select_id).val() === "Other reason") {
                    $(feedback_div_id).show();
                }
            } else {
                $(reason_div_id).hide();
                $(feedback_div_id).hide();
            }
        }
    }

    $(".diff-select").on("change", function() {
        handle_task_change($(this));
    });

    $("#diagram-type").on("change", function() {
        if (this.value !== "Dialogue System") {
            $('.fail-reason-task-container').hide();
            $('.difficulty-feedback-container').hide();
        } else {
            $(".diff-select").each(function() {
                handle_task_change($(this));
            });
        }
    });

    $(".reason-select").on("change", function() {
        let select_id = $(this).attr("id");
        let task_no = select_id.substring(select_id.lastIndexOf("-") + 1);
        if (task_no) {
            let feedback_div_id = "#fail-feedback-task-" + task_no + "-container";
            if (this.value === "Other reason") {
                $(feedback_div_id).show();
            } else {
                $(feedback_div_id).hide();
            }
        }
    });

    let bar_tags_field = $('#inputCurBarTags');

    bar_tags_field.on("keypress", function (e) {
        if (e.which === 13) {
            $("#submit-curBarTags").click();
        }
    });

    bar_tags_field.on("click", function () {
        if (bar_tags_field.val() === 'No Tags') {
            bar_tags_field.select();
        }
    });

});
