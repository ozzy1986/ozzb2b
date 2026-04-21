<?php
/**
 * Cron file.
 *
 * @package CORE\Cron
 */

// Exit if accessed directly.
defined( 'ABSPATH' ) || exit;

/**
 * Lauch WPSCORE->init() on cron init (= on plugin activation)
 *
 * @return void
 */
function wpscore_cron_init() {
	WPSCORE()->init( true );
}

if ( ! wp_next_scheduled( 'WPSCORE_init' ) ) {
	wp_schedule_event( time(), 'twicedaily', 'WPSCORE_init' );
}
