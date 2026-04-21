<?php

// register additional field for Program
add_action( 'add_meta_boxes', function() use( $field ) {
    add_meta_box(
	    'program_exercise_meta_box', // $id
	    __( 'Время на отдых перед упражнением, секунды', 'twentytwentytwo' ), // $title
	    'show_program_exercise_meta_box', // $callback
	    'program', // $screen
	    'normal', // $context
	    'high' // $priority
	);
});
// callback functions to show those fields
function show_program_exercise_meta_box() {
	global $post;

    $exercise_meta		= get_post_meta( $post->ID, 'program_exercise_meta_box', true );
    $rest_after_meta	= get_post_meta( $post->ID, 'program_exercise_rest_after_meta_box', true );
    $duration_meta		= get_post_meta( $post->ID, 'program_exercise_duration_meta_box', true );
    //echo '<br>program exercise:<pre>' . print_r( $meta, true ) . '</pre><br>';

    // get existing exercises
    $exercises = get_posts([
    	'numberposts'      => -1,
        'category'         => 0,
        'orderby'          => 'title',
        'order'            => 'ASC',
        'include'          => array(),
        'exclude'          => array(),
        'meta_key'         => '',
        'meta_value'       => '',
        'post_type'        => 'exercise',
        'suppress_filters' => true,
    ]);
    //echo '<br>exercises:<pre>' . print_r( $exercises, true ) . '</pre><br>';
    ?>
	<input type="hidden" name="program_exercise_meta_box_nonce" value="<?php echo wp_create_nonce( basename(__FILE__) ); ?>">

	<table class="admin_program_table">
	<tbody class="sortable">

	<tr class="nosort table_heading">
		<th class="program_exercise_heading"><?php _e( 'Упражнение', 'twentytwentytwo' ); ?></th>
		<th class="program_exercise_heading"><?php _e( 'Отдых, секунды', 'twentytwentytwo' ); ?></th>
		<th colspan="2" class="program_exercise_heading"><?php _e( 'Длительность, секунды', 'twentytwentytwo' ); ?></th>
	</tr>

	<?php
	for ( $i = 0; $i < 10; $i++ ) {
		// hide row if exercise wasn't selected and it's not a first row
		$show_row = true;
		if ( empty( $exercise_meta[ $i ] ) and $i > 0 ) {
			$show_row = false;
		}

		echo '<tr>';

		// select exercise
		echo '<td class="program_exercise_wrap" id="exercise_' . $i . '" style="' . ( $show_row ? 'display: table-cell;' : 'display: none;' ) . '">';
		echo '<select name="program_exercise_meta_box[]" class="program_exercise">';
		echo '<option value="0">' . __( 'Не выбрано', 'twentytwentytwo' ) . '</option>';
		foreach ( $exercises as $post ) {
			echo '<option value="' . $post->ID . '" ' . ( $post->ID == $exercise_meta[ $i ] ? 'selected' : '' ) . '>' . $post->post_title . '</option>';
		}
		echo '</select>';
		echo '</td>';

		// set rest before this exercise
		echo '<td class="program_exercise_wrap" id="rest_after_' . $i . '"  style="' . ( $show_row ? 'display: table-cell;' : 'display: none;' ) . '">';
		echo '<input type="number" class="program_exercise_rest_after" name="program_exercise_rest_after_meta_box[]" placeholder="' . __( 'Например, 20', 'twentytwentytwo' ) . '" value="' . @$rest_after_meta[ $i ] . '">';
		echo '</td>';

		// set duration of this exercise
		echo '<td class="program_exercise_wrap" id="duration_' . $i . '"  style="' . ( $show_row ? 'display: table-cell;' : 'display: none;' ) . '">';
		echo '<input type="number" class="program_exercise_duration" name="program_exercise_duration_meta_box[]" placeholder="' . __( 'Например, 60', 'twentytwentytwo' ) . '" value="' . @$duration_meta[ $i ] . '">';
		echo '</td>';

		echo '<td class="add_exercise_row_button_wrap"><button class="add_exercise_row_button">+</button></td>';

		echo '</tr>';
	}
	?>

	</tbody>
	</table>

	<?php
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

    $count = count( $_POST['program_exercise_meta_box'] );
    // exclude rows with unselected exercise
    for ( $i = 0; $i < $count; $i++ ) {
    	if ( empty( $_POST['program_exercise_meta_box'][ $i ] ) ) {
    		unset( $_POST['program_exercise_meta_box'][ $i ] );
    		unset( $_POST['program_exercise_rest_after_meta_box'][ $i ] );
    		unset( $_POST['program_exercise_duration_meta_box'][ $i ] );
    	}
    }
    // reindex arrays
    $_POST['program_exercise_meta_box']				= array_values( $_POST['program_exercise_meta_box'] );
    $_POST['program_exercise_rest_after_meta_box']	= array_values( $_POST['program_exercise_rest_after_meta_box'] );
    $_POST['program_exercise_duration_meta_box']	= array_values( $_POST['program_exercise_duration_meta_box'] );
    //echo '<br>POST:<pre>' . print_r( $_POST, true ) . '</pre><br>'; exit;

    // save exercise
	if ( isset( $_POST['program_exercise_meta_box'] ) ) {
		update_post_meta( $post_id, 'program_exercise_meta_box', $_POST['program_exercise_meta_box'] );
	}
    // save rest before
	if ( isset( $_POST['program_exercise_rest_after_meta_box'] ) ) {
		update_post_meta( $post_id, 'program_exercise_rest_after_meta_box', $_POST['program_exercise_rest_after_meta_box'] );
	}
    // save exercise duration
	if ( isset( $_POST['program_exercise_duration_meta_box'] ) ) {
		update_post_meta( $post_id, 'program_exercise_duration_meta_box', $_POST['program_exercise_duration_meta_box'] );
	}
	
});
