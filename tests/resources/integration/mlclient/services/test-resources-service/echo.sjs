function get(context, params) {
  context.outputTypes = ["application/json"];
  return {method: "get", params: params};
}

exports.GET = get;
