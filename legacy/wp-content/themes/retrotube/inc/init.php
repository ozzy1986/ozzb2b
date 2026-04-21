<?php if( ! function_exists('is_plugin_active') ) include_once( ABSPATH . 'wp-admin/includes/plugin.php' );?>

<?php if( ! is_plugin_active('wp-script-core/wp-script-core.php') ): ?>

	<p style="text-align:center;"><?php sprintf(_e('This Theme needs <a href="%s" target="_blank">WP-Script Core</a> to be installed and activated.', 'wpst'), 'https://www.wp-script.com'); ?></p>
	<style type="text/css">
		body{
			background-color: #222;
			text-align: center;
			color:#eee;
			padding-top:150px;
			font-family: 'arial';
			font-size:16px;
		}
		a{
			color:#f0476d;
		}
	</style>

<?php die(); endif;?>

<?php if( WPSCORE()->get_product_status( 'RTT' ) != 'connected' ):?>
	<p><?php sprintf(__('Please purchase a RetroTube plan: %s', 'wpst'), 'https://www.wp-script.com/themes/retrotube-adult-tube-theme/'); ?></p>

	<style type="text/css">
		body{
			background-color: #222;
			text-align: center;
			color:#eee;
			padding-top:150px;
			font-family: 'arial';
			font-size:16px;
		}
		a{
			color:#f0476d;
		}
	</style>
<?php die(); endif;?>
