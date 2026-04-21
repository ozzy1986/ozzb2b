<?php
/**
 * WPSCORE Hooks.
 *
 * @api
 * @package CORE\admin\hooks
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Filter to add thumb and partner columns when editing posts.
 *
 * @param array $defaults Array of default columns.
 */
function wpscore_add_columns( $defaults ) {
	$defaults['thumb']   = __( 'Thumb', 'wpscore_lang' );
	$defaults['partner'] = __( 'Partner', 'wpscore_lang' );
	return $defaults;
}
add_filter( 'manage_edit-post_columns', 'wpscore_add_columns' );

/**
 * Action to add thumb and partner content in columns when editig posts.
 *
 * @param string $name The name of the column to add content in.
 */
function wpscore_columns_content( $name ) {
	global $post;
	switch ( $name ) {
		case 'thumb':
			$attachment = '';
			$attr       = '';
			if ( isset( $attachment ) && is_object( $attachment ) ) {
				$attr = array(
					'alt'   => trim( wp_strip_all_tags( $attachment->post_excerpt ) ),
					'title' => trim( wp_strip_all_tags( $attachment->post_title ) ),
				);
			}
			if ( has_post_thumbnail() ) {
				echo get_the_post_thumbnail( $post->ID, 'wpscript_thumb_admin', $attr );
			} elseif ( get_post_meta( $post->ID, 'thumb', true ) ) {
				echo wp_kses(
					'<img src="' . get_post_meta( $post->ID, 'thumb', true ) . '" width="95" height="70" alt="' . get_the_title() . '" />',
					wp_kses_allowed_html(
						array(
							'img' => array(
								'alt'    => array(),
								'class'  => array(),
								'height' => array(),
								'src'    => array(),
								'width'  => array(),
							),
						)
					)
				);
			} else {
				echo wp_kses(
					'<img src="https://res.cloudinary.com/themabiz/image/upload/wpscript/sources/admin-no-image.jpg" width="95" height="70" />',
					wp_kses_allowed_html(
						array(
							'img' => array(
								'alt'    => array(),
								'class'  => array(),
								'height' => array(),
								'src'    => array(),
								'width'  => array(),
							),
						)
					)
				);
			}
			break;
		case 'partner':
			$partner = get_post_meta( $post->ID, 'partner', true );
			echo wp_kses(
				'<img src="https://res.cloudinary.com/themabiz/image/upload/wpscript/sources/' . $partner . '.jpg" alt="' . $partner . '"/>',
				wp_kses_allowed_html(
					array(
						'img' => array(
							'alt'    => array(),
							'class'  => array(),
							'height' => array(),
							'src'    => array(),
							'width'  => array(),
						),
					)
				)
			);
			break;
	}
}
add_action( 'manage_posts_custom_column', 'wpscore_columns_content' );

/**
 * Hook to create admin thumbnails for posts listings.
 */
add_image_size( 'wpscript_thumb_admin', '95', '70', '1' );

/**
 * Update client signature when switching theme.
 *
 * @return void
 */
function wpscore_switch_theme() {
	// update site signature.
	WPSCORE()->update_client_signature();
	// call init.
	WPSCORE()->init( true );
}
add_action( 'after_switch_theme', 'wpscore_switch_theme' );

/**
 * Display admin notice when there are some WP-Script porducts updates.
 *
 * @return void
 */
function wpscript_admin_notice_updates() {
	$is_core_page      = 'toplevel_page_wpscore-dashboard' === get_current_screen()->base ? true : false;
	$available_updates = WPSCORE()->get_available_updates();
	if ( $available_updates && count( $available_updates ) > 0 ) {
		echo '<div class="notice notice-success is-dismissible">';
		if ( $is_core_page ) {
			echo '<p>Some new WP-Script products versions are available.</p>';
			echo '<p><i class="fa fa-arrow-down" aria-hidden="true"></i> Just <strong>scroll down on this page and press green update buttons</strong> to update products <i class="fa fa-arrow-down" aria-hidden="true"></i></p>';
		} else {
			echo '<p>Some new WP-Script products versions are available: </p>';
			foreach ( $available_updates as $update ) {
				if ( 'CORE' === $update['product_key'] ) {
					$update_url = 'admin.php?page=wpscore-dashboard#wp-script';
					echo '<p>&#10149; ' . esc_html( $update['product_title'] ) . ' <strong>v' . esc_html( $update['product_latest_version'] ) . '</strong> &nbsp;&bull;&nbsp; <a href="' . esc_url( $update_url ) . '">Update</a></p>';
				} else {
					$update_url    = "admin.php?page=wpscore-dashboard#{$update['product_key']}";
					$changelog_url = "https://www.wp-script.com/{$update['product_type']}/{$update['product_slug']}/#changelog";
					echo '<p>&#10149; ' . esc_html( $update['product_title'] ) . ' <strong>v' . esc_html( $update['product_latest_version'] ) . '</strong> &nbsp;&bull;&nbsp; <a href="' . esc_url( $update_url ) . '">Update</a> | <a href="' . esc_url( $changelog_url ) . '" target="_blank">Changelog</a></p>';
				}
			}
		}
		echo '</div>';
	}
}
add_action( 'admin_notices', 'wpscript_admin_notice_updates' );
