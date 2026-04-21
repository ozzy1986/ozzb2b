jQuery(document).ready(function($) {
	// when user submits post to publish
	$('.payed_post_publish_form').on('submit', function(e) {
		e.preventDefault();

		// show loading gif
		$(this).append('<div class="loading"><img class="wpp_loading_gif" src="'+payed_posts.loading+'"/></div>');

		const title		= $('#dpp_title').val();
		const content	= $('#dpp_content').val();

		$.ajax({
		    type:		'post',
		    dataType:	'json',
		    url:		payed_posts.ajax_url,
		    data:		{
		    	'title':	title,
		    	'content':	content,
		    	'nonce':	payed_posts.dpp_nonce,
		    	'action':	'process_payed_post'
		    },
		    success: function(msg) {
		        console.log('msg', msg);
		        if (msg.data.redirect) {
		        	window.location.href = msg.data.redirect;
		        } else {
			        $('.loading').hide();
			    }
		    }
		});

		return false;
	});

	// show popup with form
	$('.payed_post_publish_button').on('click', function(e) {
		e.stopPropagation();

		$('.payed_post_publish_form_wrapper').fadeIn(60);
		$('html, body').animate({
            scrollTop: $(".payed_post_publish_form").offset().top - 50
        }, 20);			
	});
	// hide popup with form
	$('body').on('click', ':not(.payed_post_publish_form)', function(e){
		e.stopPropagation();

		// close when clicked outside
		if (
			!$(e.target).parents().andSelf().is('.payed_post_publish_form') // the popup form itself
			&& !$(e.target).parents().andSelf().is('.mce-container') // mce fromatting select box
			&& !$(e.target).parents().andSelf().is('[id^="__wp-uploader"]') // wp media uploader window
		) {
			$('.payed_post_publish_form_wrapper').fadeOut(40);
		}
	});
});