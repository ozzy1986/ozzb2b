<?php
/**
* Plugin Name: Анжуманя / Simple Fitness
* Plugin URI: https://www.ozzb2b.com/
* Description: Простое управление тренировками.
* Version: 0.01
* Author: Kirill Ozeritski
* Author URI: http://ozzb2b.com/
**/

require( 'ozzsf_admin.php' );
require( 'cpt.php' );
require( 'custom_taxonomies.php' );
require( 'additional_fields/exercise.php' );
require( 'additional_fields/program.php' );

// hide content field for Exercises and Programs (too much space, no use)
//add_action( 'admin_init', 'ozzsf_hide_editor' );
function ozzsf_hide_editor() {
	remove_post_type_support( 'exercise', 'editor' );
	remove_post_type_support( 'program', 'editor' );
}


// customize template for single program page
//add_filter( 'single_template', 'ozzsf_single_program_template' );
add_filter( 'template_include', 'ozzsf_single_program_template' );
function ozzsf_single_program_template( $single_template ) {
	global $post;

	if ( @$post->post_type == 'program' ) {
		if ( wp_is_block_theme() ) {
			//$program_template = plugin_dir_path( __FILE__ ) . 'templates/single-program.html';
			$program_template = plugin_dir_path( __FILE__ ) . 'templates/single-program.php';
		} else {
	    	$program_template = plugin_dir_path( __FILE__ ) . 'templates/single-program.php';
	    }

	    if ( file_exists( $program_template ) ) {
	    	$single_template = $program_template;
	    }
	}

    return $single_template;
}

register_block_type( 'core/exercise', array(
    'api_version' => 2,
    'render_callback' => 'ozzsf_render_exercise',
) );
function ozzsf_render_exercise( $block_attributes, $content ) {
    $value = get_post_meta( get_the_ID(), 'program_exercise_meta_box', true );
    // check value is set before outputting
    if ( $value ) {
        return sprintf( "%s (%s)", $content, print_r( $value, true ) );
    } else {
        return $content;
    }
}

//add_action( 'init', 'ozzsf_register_program_template' );
function ozzsf_register_program_template() {
    $program_type_object = get_post_type_object( 'program' );
    $program_type_object->template = array(
        array( 'core/image' ),
    );
}



// Shortcode for the front-end
add_shortcode( 'ozzsf', 'show_ozzsf' );
function show_ozzsf( $atts ) {
	ob_start();
	
	echo 'Hello front!';
	
	return ob_get_clean();
}

?>