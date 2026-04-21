<?php

add_action( 'admin_enqueue_scripts', 'ozzsf_enqueue_scripts_and_styles' );
function ozzsf_enqueue_scripts_and_styles() {
	global $typenow;

	wp_register_style( 'ozzsf_admin_main_css', plugin_dir_url( __FILE__ ) . 'assets/css/admin.main.css'  );
	wp_enqueue_style( 'ozzsf_admin_main_css' );

	wp_register_script( 'ozzsf_admin_main_js', plugin_dir_url( __FILE__ ) . 'assets/js/admin.main.js', ['wp-util'] );
	wp_enqueue_script( 'ozzsf_admin_main_js' );
	wp_localize_script( 'ozzsf_admin_main_js', 'ozzsf_ajax_object', array( 'ajax_url' => admin_url( 'admin-ajax.php' ) ) );

	if ( $typenow == 'program' ) {
		wp_enqueue_script( 'jquery-ui-sortable' );
	}
}

// main menu item
add_action( 'admin_menu', 'ozzsf_menu_pages') ;
function ozzsf_menu_pages() {
	add_menu_page( __( 'Анжуманя' ), __( 'Анжуманя' ), 'manage_options', 'ozzsf' );
}

// ajax to return exercise data
add_action( 'wp_ajax_get_exercise_data', 'ozzsf_ajax_get_exercise_data' );
//add_action( 'wp_ajax_nopriv_get_exercise_data', 'ozzsf_ajax_get_exercise_data' );
function ozzsf_ajax_get_exercise_data() {
	$exercise_id	= absint( $_POST['exercise_id'] );
	$exercise		= get_post( $exercise_id, ARRAY_A );
	if ( empty( $exercise ) ) {
		wp_send_json_error( __( 'Такого упражнения не найдено', 'twentytwentytwo' ) );
	} else {
		$exercise_meta = get_post_meta( $exercise_id );
		wp_send_json_success( $exercise_meta );
	}
}