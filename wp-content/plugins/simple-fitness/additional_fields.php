<?php



// register additional field for Program
add_action( 'add_meta_boxes', function() use( $field ) {
    add_meta_box(
	    'program_exercise_meta_box', // $id
	    __( 'Время на отдых перед упражнением, минуты', 'twentytwentytwo' ), // $title
	    'show_program_exercise_meta_box', // $callback
	    'program', // $screen
	    'normal', // $context
	    'high' // $priority
	);
});
// callback functions to show those fields
function show_program_exercise_meta_box() {
	global $post;  
    $meta = get_post_meta( $post->ID, 'program_exercise_meta_box', true );
    //echo '<br>program exercise:<pre>' . print_r( $meta, true ) . '</pre><br>';
    ?>
	<input type="hidden" name="program_exercise_meta_box_nonce" value="<?php echo wp_create_nonce( basename(__FILE__) ); ?>">

	<div class="program_exercise_heading"><?php _e( 'Упражнение', 'twentytwentytwo' ); ?></div>
	<div class="program_exercise_heading"><?php _e( 'Отдых перед упражнением, мин', 'twentytwentytwo' ); ?></div>
	<div class="program_exercise_heading"><?php _e( 'Длительность упражнения, мин', 'twentytwentytwo' ); ?></div>

	<?php
	for ( $i = 0; $i < 20; $i++ ) {
		// select exercise
		echo '<div class="program_exercise_wrap" id="exercise_' . $i . '">';
		echo '<input type="number" name="program_exercise_meta_box[]" placeholder="' . __( 'Например, 1', 'twentytwentytwo' ) . '" value="' . @$meta[ $i ] . '">';
		echo '</div>';

		// set rest before this exercise
		echo '<div class="program_exercise_wrap" id="rest_before_' . $i . '">';
		echo '<input type="number" name="program_exercise_rest_before_meta_box[]" placeholder="' . __( 'Например, 2', 'twentytwentytwo' ) . '" value="' . @$meta[ $i ] . '">';
		echo '</div>';

		// set duration of this exercise
		echo '<div class="program_exercise_wrap" id="duration_' . $i . '">';
		echo '<input type="number" name="program_exercise_duration_meta_box[]" placeholder="' . __( 'Например, 1', 'twentytwentytwo' ) . '" value="' . @$meta[ $i ] . '">';
		echo '</div>';

		echo '<div class="add_exercise_row_button_wrap"><button class="add_exercise_row_button">+</button></div>';
	}
}
// save this meta box to Program
add_action( 'save_post', function( $post_id ) use( $field ) {
	if ( empty( $_POST['post_type'] ) or 'program' !== $_POST['post_type'] ) {
		return $post_id;
	}
	
	// verify nonce
	if ( empty( $_POST[ 'program_exercise_meta_box_nonce' ] ) or !wp_verify_nonce( $_POST[ 'program_exercise_meta_box_nonce' ], basename(__FILE__) ) ) {
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

    //echo '<br>POST:<pre>' . print_r( $_POST, true ) . '</pre><br>'; exit;

    // save exercise
	if ( isset( $_POST[ 'program_exercise_meta_box' ] ) ) {
		update_post_meta( $post_id, 'program_exercise_meta_box', $_POST[ 'program_exercise_meta_box' ] );
	}
    // save rest before
	if ( isset( $_POST[ 'program_exercise_rest_before_meta_box' ] ) ) {
		update_post_meta( $post_id, 'program_exercise_rest_before_meta_box', $_POST[ 'program_exercise_rest_before_meta_box' ] );
	}
    // save exercise duration
	if ( isset( $_POST[ 'program_exercise_duration_meta_box' ] ) ) {
		update_post_meta( $post_id, 'program_exercise_duration_meta_box', $_POST[ 'program_exercise_duration_meta_box' ] );
	}
	
});
