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
                if (task_no) {
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

    $(".diff-select").on("change", function() {
        let select_id = $(this).attr("id");
        let task_no = select_id.substring(select_id.lastIndexOf("-") + 1);
        if (task_no) {
            let reason_div_id = "#fail-reason-task-" + task_no + "-container";
            let feedback_div_id = "#fail-feedback-task-" + task_no + "-container";
            if (this.value === "No, I failed to complete the task") {
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
