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

				<div class="author-block">
					<div class="author-display-name"><?php echo get_the_author_meta( 'display_name' ); ?></div> 
					<div class="author-videos"><i class="fa fa-play-circle"></i> <?php echo count_user_posts(get_the_author_meta('ID')); ?> <?php esc_html_e('videos', 'wpst'); ?></div>
					<div class="clear"></div>				
					<?php the_archive_description( '<div class="author-description">', '</div>' ); ?>
				</div>
			
				<h1 class="widget-title"><i class="fa fa-video-camera"></i><?php esc_html_e('Videos by:', 'wpst'); ?> <?php echo get_the_author_meta( 'display_name' ); ?></h1>
			</header><!-- .page-header -->

            <div class="videos-list">
                <?php
                /* Start the Loop */
                while ( have_posts() ) : the_post();

					get_template_part( 'template-parts/loop', 'video' );

                endwhile; ?>
            </div>

			<?php wpst_page_navi();			

		} else {

			get_template_part( 'template-parts/content', 'none' );

		} ?>

		</main><!-- #main -->
	</div><!-- #primary -->

<?php
get_sidebar();
get_footer();