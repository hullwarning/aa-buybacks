$(function () {
  $("#id_item_type").autoComplete({
    resolverSettings: {
      url: "/buybacks/item_autocomplete/",
    },
  });
});
