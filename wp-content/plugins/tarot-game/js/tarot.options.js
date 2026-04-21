jQuery(document).ready(function ($) {
	var mediaUploader;

	
	function recalculate_card_numbers() {
		console.log('boop');
		$('.tarot_card_image_preview').each(function(i) {
			i++;
			i = (i < 10) ? '&nbsp;'+i+'&nbsp;' : i;
			$(this).find('em').html(i);
		});
		$('#checked_action em').html('');
	}
	
	$('#check_all').click(function () {
		$('.check_row').not(this).prop('checked', this.checked);
		console.log(this.checked);
		if (this.checked) {
			$('.check_row').not(this).parents('.tarot_card_image_preview').addClass('checked');
		} else {
			$('.check_row').not(this).parents('.tarot_card_image_preview').removeClass('checked');
		}
	});
	$('input.check_row:checkbox, #check_all').click(function() {
		if ($('.check_row[type="checkbox"]:checked').length) {
			$('#checked_action').fadeIn(100);
			console.log(this.checked);
			if (this.checked) {
				$(this).parents('.tarot_card_image_preview').addClass('checked');
			} else {
				$(this).parents('.tarot_card_image_preview').removeClass('checked');
			}
			$('#checked_action em').html($('.check_row[type="checkbox"]:checked').length+' card'+(($('.check_row[type="checkbox"]:checked').length>1)?'s':''));
		} else {
			$('#checked_action').fadeOut(100);
		}
	});
	$('#delete_many_cards').click(function() {
		if ($('.check_row:checked').length) {
			if (confirm('Are you sure you want to delete those cards?')) {
				$('.check_row:checked').each(function() {
					$('#image_card_'+$(this).val()).remove();
				});
				recalculate_card_numbers();
				$('#check_all').removeProp('checked');
			} else {
				return false;
			}
		}
	});
		
	$('#upload-button').click(function(e) {
		e.preventDefault();
		// If the uploader object has already been created, reopen the dialog
		if (mediaUploader) {
			mediaUploader.open();
			return;
		}
		// Extend the wp.media object
		mediaUploader = wp.media.frames.file_frame = wp.media({
			title: 'Choose Images',
			button: {
				text: 'Choose Images'
			}, 
			multiple: true 
		});

		// When a file is selected, grab the URL and set it as the text field's value
		mediaUploader.on('select', function() {
			$.each(mediaUploader.state().get('selection').models, function(i, e) {
				// create input elements
				var url = e.attributes.url.replace('http://'+window.location.hostname, '');
				i++;
				i_out = (i < 10) ? '&nbsp;'+i+'&nbsp;' : i;
				var image_element = '<div class="tarot_card_image_preview" id="image_card_'+i+'">' +
				'<input type="hidden" name="tarot_card_images[]" value="'+url+'">' +
				'<img src="'+url+'" width="138" height="240">' +
				'<br><label><em>'+i_out+'</em><input type="checkbox" class="check_row" name="selected_card_images[]" value="'+i+'"></label>' +
				'<button type="submit" class="remove_image button">Remove</button>' +
				'</div>';
				$('#upload_cards').append(image_element);
			});
			recalculate_card_numbers();
		});
		// Open the uploader dialog
		mediaUploader.open();
	});
	
	// removing just uploaded card image
	$(document).on('click', '.remove_image', function(e) {
		e.preventDefault();
		if (confirm('Are you sure you want to delete the card?')) {
			$(this).parent('.tarot_card_image_preview').remove();
			recalculate_card_numbers();
		}
		
		return false;
	});
	
	// Expand card images
	$('#expand_deck').click(function() {
		$('#upload_cards').slideToggle(200);
		
		return false;
	});
	
	// The "Upload" button
	$('.upload_image_button').click(function() {
		var send_attachment_bkp = wp.media.editor.send.attachment;
		var button = $(this);
		wp.media.editor.send.attachment = function(props, attachment) {
			$(button).parent().prev().attr('src', attachment.url);
			$(button).prev().val(attachment.id);
			wp.media.editor.send.attachment = send_attachment_bkp;
		}
		wp.media.editor.open(button);
		return false;
	});

	// The "Remove" button (remove the value from input type='hidden')
	$('.remove_image_button').click(function() {
		var answer = confirm('Are you sure?');
		if (answer == true) {
			var src = $(this).parent().prev().attr('data-src');
			$(this).parent().prev().attr('src', src);
			$(this).prev().prev().val('');
		}
		return false;
	});
});