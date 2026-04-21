<?php
/**
 * Template Name: Tags
 **/
get_header(); ?>

<?php
if ( xbox_get_field_value( 'wpst-options', 'show-sidebar' ) == 'on' ) {
	if ( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) {
		$sidebar_pos = 'with-sidebar-right';
	} else {
		$sidebar_pos = 'with-sidebar-left'; }
} else {
	$sidebar_pos = '';
}
?>

	<div id="primary" class="content-area <?php echo $sidebar_pos; ?> categories-list">
		<main id="main" class="site-main <?php echo $sidebar_pos; ?>" role="main">

		<header class="entry-header">
			<?php the_title( '<h1 class="widget-title"><i class="fa fa-tags"></i>', '</h1>' ); ?>
		</header>

		<?php the_content(); ?>

		<?php
			$args = array(
				'smallest'                  => 12,
				'largest'                   => 24,
				'unit'                      => 'px',
				'number'                    => 1000,
				'format'                    => 'flat',
				'separator'                 => '',
				'orderby'                   => 'name',
				'order'                     => 'ASC',
				'exclude'                   => null,
				'include'                   => null,
				'topic_count_text_callback' => 'default_topic_count_text',
				'link'                      => 'view',
				'taxonomy'                  => 'post_tag',
				'echo'                      => true,
				'child_of'                  => null,
			);
			?>
		<?php wp_tag_cloud( $args ); ?>

		</main><!-- #main -->
	</div><!-- #primary -->

<?php
get_sidebar();
get_footer();
