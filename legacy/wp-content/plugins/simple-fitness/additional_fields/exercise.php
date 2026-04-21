<?php

// additional fields for Exercise
$excercise_additional_fields = [
	[
		'id'			=> 'exercise_rest_before_meta_box',
		'title'			=> __( 'Отдых до, секунды', 'twentytwentytwo' )
	],
	[
		'id'			=> 'exercise_duration_meta_box',
		'title'			=> __( 'Время на выполнение, секунды', 'twentytwentytwo' )
	],
	[
		'id'			=> 'exercise_rest_after_meta_box',
		'title'			=> __( 'Отдых после, секунды', 'twentytwentytwo' )
	]
];
// callback functions to show those fields
function show_exercise_rest_before_meta_box() {
	global $post;  
    $meta = get_post_meta( $post->ID, 'exercise_rest_before_meta_box', true );
    ?>

	<input type="hidden" name="exercise_rest_before_meta_box_nonce" value="<?php echo wp_create_nonce( basename(__FILE__) ); ?>">

	<input type="number" name="exercise_rest_before_meta_box" placeholder="Например, 20" value="<?php echo $meta; ?>">

<?php
}
function show_exercise_duration_meta_box() {
	global $post;  
    $meta = get_post_meta( $post->ID, 'exercise_duration_meta_box', true );
    ?>

	<input type="hidden" name="exercise_duration_meta_box_nonce" value="<?php echo wp_create_nonce( basename(__FILE__) ); ?>">

	<input type="number" name="exercise_duration_meta_box" placeholder="Например, 60" value="<?php echo $meta; ?>">

<?php
}
function show_exercise_rest_after_meta_box() {
	global $post;  
    $meta = get_post_meta( $post->ID, 'exercise_rest_after_meta_box', true );
    ?>

	<input type="hidden" name="exercise_rest_after_meta_box_nonce" value="<?php echo wp_create_nonce( basename(__FILE__) ); ?>">

	<input type="number" name="exercise_rest_after_meta_box" placeholder="Например, 90" value="<?php echo $meta; ?>">

<?php
}

foreach ( $excercise_additional_fields as $field ) {
	// register additional field for Excercise
	add_action( 'add_meta_boxes', function() use( $field ) {
	    add_meta_box(
		    $field['id'], // $id
		    $field['title'], // $title
		    'show_' . $field['id'], // $callback
		    'exercise', // $screen
		    'normal', // $context
		    'high' // $priority
		);
	});

	// save this meta box
	add_action( 'save_post', function( $post_id ) use( $field ) {
		if ( empty( $_POST['post_type'] ) or 'exercise' !== $_POST['post_type'] ) {
			return $post_id;
		}
		
		// verify nonce
		if ( empty( $_POST[ $field['id'] . '_nonce' ] ) or !wp_verify_nonce( $_POST[ $field['id'] . '_nonce' ], basename(__FILE__) ) ) {
		    return $post_id; 
		}
		// check autosave
		if ( defined( 'DOING_AUTOSAVE' ) and DOING_AUTOSAVE ) {
		    return $post_id;
		}
		
	    if ( !current_user_can( 'edit_page', $post_id ) ) {
	        return $post_id;
	    } elseif ( !current_user_can( 'edit_post', $post_id ) ) {
	        return $post_id;
	    }

		$old = get_post_meta( $post_id, $field['id'], true );
		$new = absint( $_POST[ $field['id'] ] );

		if ( $new and $new !== $old ) {
		    update_post_meta( $post_id, $field['id'], $new );
		} elseif ( '' === $new and $old ) {
		    delete_post_meta( $post_id, $field['id'], $old );
		}
	});
}
