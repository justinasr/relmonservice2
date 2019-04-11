function createRelmon() {
  var data = {};
  data['name'] = $("#relmon_name").val();
  data['categories'] = []

  data_reference = $("#data_reference").val().split('\n').filter(Boolean);
  data_target = $("#data_target").val().split('\n').filter(Boolean);
  if (data_reference.length > 0 && data_target.length > 0) {
    data_category = {name: 'Data',reference: data_reference, target: data_target};
    data_category['HLT'] = $('#data_hlt').val()
    data_category['automatic_pairing'] = $('#data_pairing').val() === 'automatic'
    data['categories'].push(data_category);
  }

  fullsim_reference = $("#fullsim_reference").val().split('\n').filter(Boolean);
  fullsim_target = $("#fullsim_target").val().split('\n').filter(Boolean);
  if (fullsim_reference.length > 0 && fullsim_target.length > 0) {
    fullsim_category = {name: 'FullSim', reference: fullsim_reference, target: fullsim_target};
    fullsim_category['HLT'] = $('#fullsim_hlt').val()
    fullsim_category['automatic_pairing'] = $('#fullsim_pairing').val() === 'automatic'
    data['categories'].push(fullsim_category);
  }

  fastsim_reference = $("#fastsim_reference").val().split('\n').filter(Boolean);
  fastsim_target = $("#fastsim_target").val().split('\n').filter(Boolean);
  if (fastsim_reference.length > 0 && fastsim_target.length > 0) {
    fastsim_category = {name: 'FastSim', reference: fastsim_reference, target: fastsim_target};
    fastsim_category['HLT'] = $('#fastsim_hlt').val()
    fastsim_category['automatic_pairing'] = $('#fastsim_pairing').val() === 'automatic'
    data['categories'].push(fastsim_category);
  }

  generator_reference = $("#generator_reference").val().split('\n').filter(Boolean);
  generator_target = $("#generator_target").val().split('\n').filter(Boolean);
  if (generator_reference.length > 0 && generator_target.length > 0) {
    generator_category = {name: 'Generator', reference: generator_reference, target: generator_target};
    generator_category['HLT'] = 'only'
    generator_category['automatic_pairing'] = $('#generator_pairing').val() === 'automatic'
    data['categories'].push(generator_category);
  }

  fullsim_pu_reference = $("#fullsim_pu_reference").val().split('\n').filter(Boolean);
  fullsim_pu_target = $("#fullsim_pu_target").val().split('\n').filter(Boolean);
  if (fullsim_pu_reference.length > 0 && fullsim_pu_target.length > 0) {
    fullsim_pu_category = {name: 'FullSim_PU', reference: fullsim_pu_reference, target: fullsim_pu_target};
    fullsim_pu_category['HLT'] = $('#fullsim_pu_hlt').val()
    fullsim_pu_category['automatic_pairing'] = $('#fullsim_pu_pairing').val() === 'automatic'
    data['categories'].push(fullsim_pu_category);
  }

  fastsim_pu_reference = $("#fastsim_pu_reference").val().split('\n').filter(Boolean);
  fastsim_pu_target = $("#fastsim_pu_target").val().split('\n').filter(Boolean);
  if (fastsim_pu_reference.length > 0 && fastsim_pu_target.length > 0) {
    fastsim_pu_category = {name: 'FastSim_PU', reference: fastsim_pu_reference, target: fastsim_pu_target};
    fastsim_pu_category['HLT'] = $('#fastsim_pu_hlt').val()
    fastsim_pu_category['automatic_pairing'] = $('#fastsim_pu_pairing').val() === 'automatic'
    data['categories'].push(fastsim_pu_category);
  }

  console.log('Creating relmon...')
  console.log(data);
  $.ajax({
    type: "POST",
    url: "/create",
    contentType: "application/json",
    data: JSON.stringify(data),
  }).done(function (data) {
    console.log(data)
  }).fail(function(data) {
    console.log(data)
  });
}

function tick() {
  console.log('Tick')
  $.ajax({
    type: "GET",
    url: "/tick",
  }).done(function (data) {
    console.log(data)
  }).fail(function(data) {
    console.log(data)
  });
}

function resetRelmon(relmonID) {
  console.log('Reset ' + relmonID)
  $.ajax({
    type: "POST",
    url: "/reset",
    contentType: "application/json",
    data: JSON.stringify({id: relmonID}),
  }).done(function (data) {
    console.log(data)
  }).fail(function(data) {
    console.log(data)
  });
}

function deleteRelmon(relmonID) {
  console.log('Delete ' + relmonID)
  $.ajax({
    type: "DELETE",
    url: "/delete",
    contentType: "application/json",
    data: JSON.stringify({id: relmonID}),
  }).done(function (data) {
    console.log(data)
  }).fail(function(data) {
    console.log(data)
  });
}