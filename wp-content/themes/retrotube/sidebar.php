<?php
if ( /*!is_active_sidebar( 'sidebar' ) ||*/ wp_is_mobile() && xbox_get_field_value( 'wpst-options', 'show-sidebar-mobile' ) == 'off' ) {
	return;
} ?>

<?php if( is_home() ) {
	$show_sidebar = xbox_get_field_value( 'wpst-options', 'show-sidebar-homepage' );
} elseif( is_single() ) {
	$show_sidebar = xbox_get_field_value( 'wpst-options', 'show-sidebar-video-page' );
} elseif( is_page_template('template-categories.php') ) {
	$show_sidebar = xbox_get_field_value( 'wpst-options', 'show-sidebar-categories-page' );
} else {
	$show_sidebar = xbox_get_field_value( 'wpst-options', 'show-sidebar' );
} ?>

<?php if( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) {
	$sidebar_pos = 'with-sidebar-right';
} else {
	$sidebar_pos = 'with-sidebar-left';
} ?>

<?php if( $show_sidebar == 'on' ) : ?>
	<aside id="sidebar" class="widget-area <?php echo $sidebar_pos; ?>" role="complementary">
		<?php if(wp_is_mobile() && xbox_get_field_value( 'wpst-options', 'sidebar-ad-mobile' ) != '') : ?>
			<div class="happy-sidebar">
				<?php echo wpst_render_shortcodes( xbox_get_field_value( 'wpst-options', 'sidebar-ad-mobile' ) ); ?>
			</div>
		<?php elseif(xbox_get_field_value( 'wpst-options', 'sidebar-ad-desktop' ) != '') : ?>
			<div class="happy-sidebar">
				<?php echo wpst_render_shortcodes( xbox_get_field_value( 'wpst-options', 'sidebar-ad-desktop' ) ); ?>
			</div>
		<?php endif; ?>
		<?php dynamic_sidebar( 'sidebar' ); ?>
	</aside><!-- #sidebar -->
<?php endif; ?>
