<?php

// ajax process data submitted when user publishes payed post
add_action( 'wp_ajax_nopriv_process_payed_post', 'process_payed_post' );
add_action( 'wp_ajax_process_payed_post', 'process_payed_post' );
function process_payed_post() {
	if ( !wp_verify_nonce( @$_POST['nonce'], 'dpp-nonce') ) {
		wp_send_json_error( __( 'Not authorized attempt.', 'payed-posts' ) );
		wp_die ( 'Busted!' );
	}
    //echo "\n " . ' <br>post:<pre> ' . print_r( $_POST, true ) . ' </pre><br> ' . " \n";

	// sanitize input data
	$title		= sanitize_text_field( @$_POST['title'] );
    $content	= sanitize_post( @$_POST['content'], 'db' );

    // check if it's empty
    if ( empty( $title ) and empty( $content ) ) {
    	wp_send_json_error( __( 'Post is empty.', 'payed-posts' ) );
    	wp_die();
    }

	// create post draft before payment complete
	$post_id = dpp_create_payed_post( $title, $content );
    
    // create order for payed post product
	$order_result = create_order_payed_post( $post_id );
	//echo "\n " . ' <br>order_result:<pre> ' . print_r( $order_result, true ) . ' </pre><br> ' . " \n";
	if ( $order_result['result'] == 'success' and !empty( $order_result['redirect'] ) ) {
		wp_send_json_success( ['redirect' => $order_result['redirect'] ] );
	}

    //    wp_die();
}

// simply creates post
function dpp_create_payed_post( $title, $content ) {
	$new_post = array(
		'post_title'		=> $title,
		'post_content'		=> $content,
		'post_status'		=> 'draft',
		'post_date'			=> date( 'Y-m-d H:i:s' ),
		//'post_author'		=> $user_ID,
		'post_type'			=> 'post',
		'post_category'		=> array(0)
	);
	$post_id = wp_insert_post( $new_post );

	return $post_id;
}

// process submitted comment
add_action( 'comment_post', 'dpp_process_payed_comment', 10, 2 );
function dpp_process_payed_comment( $comment_id, $comment_approved ) {
	// first place this comment on hold before payment
	wp_set_comment_status( $comment_id, 'hold' );
	
	// create order for payed comment product
	$order_result = create_order_payed_post( $comment_id, 'comment' );
	if ( $order_result['result'] == 'success' and !empty( $order_result['redirect'] ) ) {
		// redirect to payment gateway
		header( 'Location: ' . $order_result['redirect'] );
		exit;
	}
}