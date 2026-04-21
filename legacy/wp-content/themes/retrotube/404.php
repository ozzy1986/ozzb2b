<?php get_header(); ?>

<?php if( xbox_get_field_value( 'wpst-options', 'show-sidebar' ) == 'on') {
	if( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) { $sidebar_pos = 'with-sidebar-right'; } else { $sidebar_pos = 'with-sidebar-left'; }
}else{
	$sidebar_pos = '';
} ?>

	<div id="primary" class="content-area <?php echo $sidebar_pos; ?>">
		<main id="main" class="site-main <?php echo $sidebar_pos; ?>" role="main">

			<section class="error-404 not-found">
				<header class="page-header">
					<h1 class="widget-title"><?php esc_html_e( 'Oops! That page can&rsquo;t be found.', 'wpst' ); ?></h1>
				</header><!-- .page-header -->

				<div class="page-content">
					<p><?php esc_html_e( 'It looks like nothing was found at this location. Maybe try one of the links below or a search?', 'wpst' ); ?></p>

					<?php get_search_form(); ?>

					<div class="notfound-videos">
						<h2 class="widget-title"><?php esc_html_e('Random videos'); ?></h2>
						<div>
						<?php $args = array( 'numberposts' => xbox_get_field_value( 'wpst-options', 'videos-per-page' ), 'orderby' => 'rand' );
						$rand_posts = get_posts( $args );				
						foreach( $rand_posts as $post ) { 
							get_template_part( 'template-parts/loop', 'video' );
						} ?>
						</div>
					</div>
				</div><!-- .page-content -->
			</section><!-- .error-404 -->

		</main><!-- #main -->
	</div><!-- #primary -->

<?php
get_sidebar();
get_footer();