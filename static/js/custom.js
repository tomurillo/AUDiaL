$(function () {
    $('#navtabs a').on("click", function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    $('#inputRetrieve').on("keypress", function(e) {
        if (e.which === 13) {
            $("#submit-retrieve").click();
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

    let alert_msg_div = $('#alert-message');

    if(alert_msg_div.length)  {
        alert_msg_div.focus();
    }

});
