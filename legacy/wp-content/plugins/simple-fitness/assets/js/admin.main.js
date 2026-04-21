jQuery(document).ready(function($) {
	// make exercise table in training program sortable
	$('.sortable').sortable({
		start: function( event, ui ) {
			// hide add button
			$('.add_exercise_row_button_wrap').hide();
		},
		stop: function( event, ui ) {
			// show only the last add button
			showLastAddButton();
		},
		items: 'tr:not(.nosort)'
	});

	showLastAddButton();

	// add exercise row in program edit page
	$('.add_exercise_row_button').on('click', function() {
		$(this).parent().hide().parent('tr').next('tr').children().slideDown(200).children('tr.add_exercise_row_button').show();
		// hide next button if no more rows
		if (!$(this).parent().parent('tr').next('tr').length) {
			$(this).parent().parent('tr').next('tr').children('tr.add_exercise_row_button').hide();
		}

		return false;
	});

	// load exercise's duration and rest before when selecting exercise
	$('.program_exercise').on('change', function() {
		/*jQuery.ajax({
			type: 'post',
		    dataType: 'json',
		    url: ozzsf_ajax_object.ajax_url,
		    data: {
		    	action: 'get_exercise_data',
		    	exercise_id: $(this).val()
		    },
		    success: function(msg) {
		        console.log('msg', msg);
		    }
		});*/
		const exerciseSelect = $(this);
		wp.ajax.post( 'get_exercise_data', {
	    	action: 'get_exercise_data',
	    	exercise_id: $(this).val()
	    } ).done(function(response) {
			// set default duration and rest before if they weren't set by user yet
			if (response.exercise_duration_meta_box && exerciseSelect.parent().next().next().children('input').val() == '') {
				exerciseSelect.parent().next().next().children('input').val(response.exercise_duration_meta_box[0]);
			}
			if (response.exercise_rest_before_meta_box && exerciseSelect.parent().next().children('input').val() == '') {
				exerciseSelect.parent().next().children('input').val(response.exercise_rest_before_meta_box[0]);
			}
		});

	});

	// show only add button for the last row if it ain't the last at all
	function showLastAddButton() {
		$('.add_exercise_row_button_wrap').hide();
		if ($('.program_exercise_wrap:visible:last').parent().next('tr').length) {
			$('.program_exercise_wrap:visible:last').next('.add_exercise_row_button_wrap').show();
		}
	}
});