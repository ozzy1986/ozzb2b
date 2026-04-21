<?php

/**

* Plugin Name: Payed posts

* Description: Users can publish posts for payment.

* Version: 0.01

* Domain Path: /languages

* Author: Kirill Ozeritski

**/



// plugin activation hooks

require_once( plugin_dir_path( __FILE__ ) . '/on_activation.php' );

register_activation_hook( __FILE__, 'dpp_create_payed_post_product' );

register_activation_hook( __FILE__, 'dpp_create_payed_comment_product' );



require_once( plugin_dir_path( __FILE__ ) . '/process_post.php' );

require_once( plugin_dir_path( __FILE__ ) . '/order.php' );



// load localization

add_action( 'init', 'dpp_load_plugin_textdomain' );

function dpp_load_plugin_textdomain() {

    $is_loaded = load_plugin_textdomain(

        'payed-posts',

        false,

        dirname( plugin_basename(__FILE__) ) . '/languages/'

    );

    //echo '<br>is_loaded: ' . $is_loaded . '<br>'; exit;

}



// register javascripts and styles

add_action( 'wp_enqueue_scripts', 'dpp_enqueue' );

function dpp_enqueue() {

	wp_register_script( 'dpp-script', plugin_dir_url(__FILE__) . 'assets/js/payed_posts.js', ['jquery'], '1.0.0' );

	wp_localize_script( 'dpp-script', 'payed_posts', [

		//'ajax_url'	=> admin_url( 'admin-ajax.php', 'http' ),

		'ajax_url'	=> admin_url( 'admin-ajax.php' ),

		'dpp_nonce'	=> wp_create_nonce('dpp-nonce'),

		'loading'	=> plugin_dir_url(__FILE__) . 'assets/img/loading.gif'

	]);



	wp_register_style( 'dpp-style', plugin_dir_url(__FILE__) . 'assets/css/payed_posts.css', [], '1.0.0', 'all' );

}



// shortcode for button and a form to submit payed post

add_shortcode( 'dur_payed_publish', 'show_payed_publish_form_and_button' );

function show_payed_publish_form_and_button( $atts ) {



	wp_enqueue_script( 'dpp-script' );

	wp_enqueue_style( 'dpp-style' );



	ob_start();

	?>



	<div class="payed_post_publish_button_wrapper">

		<button class="payed_post_publish_button"><?php _e( 'Publish for durcoin' , 'payed-posts' ); ?></button>

	</div>



	<div class="payed_post_publish_form_wrapper" style="display: none;">

		<div class="payed_post_publish_form_bg"></div>

		<form class="payed_post_publish_form">

			<div class="title_wrapper">

				<input type="text" size="40" name="dpp_title" id="dpp_title" placeholder="<?php _e( 'Title placeholder', 'payed-posts' ); ?>" />

			</div>

			<div class="content_wrapper">

				<?php

				$args = array(

				    /*'tinymce'       => array(

				        'toolbar1'      => 'bold,italic,underline,separator,alignleft,aligncenter,alignright,separator,link,unlink,undo,redo',

				        'toolbar2'      => '',

				        'toolbar3'      => '',

				    ),*/

				);

				wp_editor( '', 'dpp_content', $args );

				?>

			</div>



			<div class="submit_wrapper">

				<button class="submit dpp_submit"><?php _e( 'Submit' , 'payed-posts' ); ?></button>

			</div>

		</form>

	</div>





	<?

	return ob_get_clean();

}

