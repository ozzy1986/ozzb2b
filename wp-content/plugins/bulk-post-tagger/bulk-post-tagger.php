<?php
/*
Plugin Name:  Bulk Post Tagger
Description:  Adds tags to list of posts by url.
Version:      1.0
Author:       ozzy1986
Author URI:   https://profiles.wordpress.org/ozzy1986
*/

defined( 'ABSPATH' ) or die( 'No script kiddies please!' ); // blocking direct access

add_action( 'admin_menu', 'mass_tag_game_menu' );
function mass_tag_game_menu() {
	//add_menu_page( 'Bulk tag', 'Bulk Post Tagger', 'edit_posts', 'mass-tag', 'mass_tag_options', 'dashicons-format-gallery' );
	add_submenu_page( 'tools.php', 'Bulk tag', 'Bulk tag', 'edit_posts', 'mass-tag', 'mass_tag_options', 10 );
}

function mass_tag_options() {
	if ( !current_user_can( 'edit_posts' ) )  {
		wp_die( __( 'You do not have sufficient permissions to access this page.' ) );
	}
	
	// WordPress library
    //wp_enqueue_media();
	//wp_enqueue_script( 'options-script', plugin_dir_url( __FILE__ ) . 'js/tarot.options.js', array( 'jquery' ) );
	//wp_enqueue_style( 'tarot-style', plugin_dir_url( __FILE__ ) . 'tarot.style.css' );
	
	require_once plugin_dir_path( __FILE__ ) . 'mass-tag-options.php';
}


// add tags to pages
if ( !function_exists( 'tagpages_register_taxonomy' ) ) {
	function tagpages_register_taxonomy() {
		register_taxonomy_for_object_type( 'post_tag', 'page' );
	}
	add_action( 'init', 'tagpages_register_taxonomy' );
}

// add tags to pages in queries
if ( !function_exists( 'tags_support_query' ) ) {
	function tags_support_query( $query ) {
		if ( $query->get('tag') ) { 
			$query->set('post_type', 'any');
		}
	}
	add_action( 'pre_get_posts', 'tags_support_query' );
}

