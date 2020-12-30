$(function () {
  $("#notify").on("click", function () {
    var items = {};

    $("#value tbody tr").each(function () {
      var id = $(this).find("td").eq(0).attr("data-type-id");
      var quantity = $(this).find("td").eq(1).text();

      items[id] = parseInt(quantity.replace(/,/g, ""), 10);
    });

    var total = parseInt($("#total").text().replace(/,/g, ""), 10);

    var program_location = $(this).attr("data-program-location");
    var url = $(this).attr("data-url");

    $.ajax({
      url: url,
      type: "post",
      dataType: "json",
      contentType: "application/json",
      success: function () {
        window.location.href = "/buybacks";
      },
      data: JSON.stringify({
        items: items,
        total: total,
        program_location: program_location,
      }),
    });
  });
});
