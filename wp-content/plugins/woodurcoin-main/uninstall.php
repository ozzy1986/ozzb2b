<?php

/**
 * @since      1.0.0
 * @package    Woodurcoin
 * @author     granvik
 */

// If uninstall not called from WordPress, then exit.
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

// Delete plugin options
delete_option('woocommerce_woodurcoin_settings');

// Delete post meta
$woodurcoin_post_args = array(
    'posts_per_page' => -1,
    'post_type' => 'shop_order'
);
$woodurcoin_posts = get_posts($woodurcoin_post_args);
foreach ($woodurcoin_posts as $post) {
	delete_post_meta($post->ID, 'durcoin_total');
	delete_post_meta($post->ID, 'durcoin_attachment');
}