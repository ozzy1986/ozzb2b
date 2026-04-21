<?php
/*
Plugin Name:  Tarot Game
Plugin URI:   https://developer.wordpress.org/plugins/tarot-game/
Description:  Adds Simple Tarot Game
Version:      1.0
Author:       ozzy1986
Author URI:   https://profiles.wordpress.org/ozzy1986
License:      GPL2
License URI:  https://www.gnu.org/licenses/gpl-2.0.html
Text Domain:  wporg
Domain Path:  /languages
*/

defined( 'ABSPATH' ) or die( 'No script kiddies please!' ); // blocking direct access

add_action( 'admin_menu', 'tarot_game_menu' );
function tarot_game_menu() {
	add_menu_page( 'Tarot Game Options', 'Tarot Game', 'manage_options', 'tarot-game', 'tarot_game_options', 'dashicons-format-gallery' );
}

function tarot_game_options() {
	if ( !current_user_can( 'manage_options' ) )  {
		wp_die( __( 'You do not have sufficient permissions to access this page.' ) );
	}
	
	// WordPress library
    wp_enqueue_media();
	wp_enqueue_script( 'options-script', plugin_dir_url( __FILE__ ) . 'js/tarot.options.js', array( 'jquery' ) );
	wp_enqueue_style( 'tarot-style', plugin_dir_url( __FILE__ ) . 'tarot.style.css' );
	
	require_once plugin_dir_path( __FILE__ ) . 'tarot-options.php';
}


function tarot_image_uploader( $name, $width = 0, $height = 0 ) {
    
	// Set variables
    $option = get_option( $name );
    $default_image = plugins_url( 'images/cards/cover.png', __FILE__ );

    if ( !empty( $option ) and $option !== false ) {
        $image_attributes = wp_get_attachment_image_src( $option, 'medium' );
		//echo '<pre>' . print_r( $image_attributes, true ) . '</pre>';
        $src = $image_attributes[0];
        $value = $option;
		if ($width == 0) {
			$width = $image_attributes[1];
		}
		if ($height == 0) {
			$height = $image_attributes[2];
		}
    } else {
        $src = $default_image;
        $value = '';
		if ($width == 0) {
			$width = 101;
		}
		if ($height == 0) {
			$height = 209;
		}
    }

    $text = __( 'Upload', 'RSSFI_TEXT' );

    // Print HTML field
    echo '
        <div class="upload">
            <img data-src="' . $default_image . '" src="' . esc_url( $src ) . '" width="' . $width . 'px" height="' . $height . 'px" />
            <div>
                <input type="hidden" name="' . $name . '" id="' . $name . '" value="' . $value . '" />
                <button type="submit" class="upload_image_button button">' . $text . '</button>
                <button type="submit" class="remove_image_button button">&times;</button>
            </div>
        </div>
    ';
}


// Add shortcode
add_shortcode( 'tarot_game', 'show_tarot_game' );
$tarot_shortcode_parameters = array(
	'above_before' 	=> nl2br( get_option('tarot_html_above_before_draw') ),
	'below_before' 	=> nl2br( get_option('tarot_html_below_before_draw') ),
	'below_after' 	=> nl2br( get_option('tarot_html_below_after_draw') )
);
function show_tarot_game( $atts, $content = null ) {
	global $tarot_shortcode_parameters;
	// include js and css
	wp_enqueue_style( 'tarot-style', plugin_dir_url( __FILE__ ) . 'tarot.style.css' );
	wp_enqueue_script( 'tarot-script', plugin_dir_url( __FILE__ ) . 'js/tarot.game.js', array( 'jquery' ) );
	
	if ( !empty( $content ) ) {
		do_shortcode( $content );
	} else {
		// shortcode attributes for HTMLs
		$tarot_shortcode_parameters = shortcode_atts( array(
			'above_before' 	=> nl2br( get_option( 'tarot_html_above_before_draw' ) ),
			'below_before' 	=> nl2br( get_option( 'tarot_html_below_before_draw' ) ),
			'below_after' 	=> nl2br( get_option( 'tarot_html_below_after_draw' ) )
		), $atts );
	}
	
	// remove stupid paragraph formatting
	$tarot_shortcode_parameters['above_before']	= trim( preg_replace( '/\<p\>|\<\/p\>/', '', $tarot_shortcode_parameters['above_before'] ) );
	$tarot_shortcode_parameters['below_before']	= trim( preg_replace( '/\<p\>|\<\/p\>/', '', $tarot_shortcode_parameters['below_before'] ) );
	$tarot_shortcode_parameters['below_after']	= trim( preg_replace( '/\<p\>|\<\/p\>/', '', $tarot_shortcode_parameters['below_after'] ) );

	
	require_once plugin_dir_path( __FILE__ ) . 'tarot-display.php'; // here the $output is generated
	
    return $output;
}

add_shortcode( 'tarot_above_before', 'show_tarot_above_before' );
function show_tarot_above_before( $atts, $content = null ) {
    global $tarot_shortcode_parameters;
	$tarot_shortcode_parameters['above_before'] = $content;
}

add_shortcode( 'tarot_below_before', 'show_tarot_below_before' );
function show_tarot_below_before( $atts, $content = null ) {
    global $tarot_shortcode_parameters;
	$tarot_shortcode_parameters['below_before'] = $content;
}

add_shortcode( 'tarot_below_after', 'show_tarot_below_after' );
function show_tarot_below_after( $atts, $content = null ) {
    global $tarot_shortcode_parameters;
	$tarot_shortcode_parameters['below_after'] = $content;
}