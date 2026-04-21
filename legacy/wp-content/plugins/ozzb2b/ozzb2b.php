<?php
/**
* Plugin Name: B2B Search
* Plugin URI: https://www.ozzb2b.com/
* Description: For easy finding outsourcing companies.
* Version: 0.01
* Author: Kirill Ozeritski
* Author URI: http://ozzb2b.com/
**/


/* START of admin part */

add_action( 'admin_menu', 'ozzb2b_menu_pages') ;
function ozzb2b_menu_pages() {

	add_menu_page('B2B Search', 'B2B Search', 'manage_options', 'ozzb2b', 'ozzb2b_admin_output', 'dashicons-buddicons-bbpress-logo' );
	//add_submenu_page('ozz-dem', 'Map Settings', 'Map Settings', 'manage_options', 'ozz-dem' );
	//add_submenu_page('ozz-dem', 'List Settings', 'List Settings', 'manage_options', 'ozz-dem2' );

}

function ozzb2b_admin_output() {
?>
	Hello
<?php

}

/* END of admin part */





// Shortcode for the front-end
add_shortcode( 'ozzb2b_search', 'show_ozzb2b_search' );
function show_ozzb2b_search( $atts ) {
	ob_start();
	
	echo 'Hello front!';
	
	return ob_get_clean();
}

?>