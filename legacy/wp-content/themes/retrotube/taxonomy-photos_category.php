<?php get_header(); ?>

<?php if( xbox_get_field_value( 'wpst-options', 'show-sidebar' ) == 'on') {
	if( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) { $sidebar_pos = 'with-sidebar-right'; } else { $sidebar_pos = 'with-sidebar-left'; }
}else{
	$sidebar_pos = '';
} ?>

	<div id="primary" class="content-area <?php echo $sidebar_pos; ?>">
		<main id="main" class="site-main <?php echo $sidebar_pos; ?>" role="main">

		<?php if ( have_posts() ) { ?>

			<header class="page-header">
				<?php
					the_archive_title( '<h1 class="widget-title">', '</h1>' );
					the_archive_description( '<div class="archive-description">', '</div>' );
				?>
			</header><!-- .page-header -->

			<?php
			/* Start the Loop */
			while ( have_posts() ) : the_post();
				get_template_part( 'template-parts/loop', 'photo' );
			endwhile;
			
			wpst_page_navi();

		} else {

			get_template_part( 'template-parts/content', 'none' );

		} ?>

		</main><!-- #main -->
	</div><!-- #primary -->

<?php
get_sidebar();
get_footer();