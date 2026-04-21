<?php
/**
 * Template Name: Blog
 **/
get_header(); ?>

<?php if( xbox_get_field_value( 'wpst-options', 'show-sidebar' ) == 'on') {
	if( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) { $sidebar_pos = 'with-sidebar-right'; } else { $sidebar_pos = 'with-sidebar-left'; }
}else{
	$sidebar_pos = '';
} ?>

	<div id="primary" class="content-area <?php echo $sidebar_pos; ?>">
		<main id="main" class="site-main <?php echo $sidebar_pos; ?>" role="main">
            <header class="page-header">
                <?php the_title( '<h1 class="widget-title"><i class="fa fa-edit"></i>', '</h1>' ); ?>             
            </header><!-- .page-header -->
            <?php $myposts = new WP_Query( array(
                    'post_type' => 'post',
                    'tax_query' => array(
                        array(
                            'taxonomy' => 'post_format',
                            'operator' => 'NOT EXISTS',
                        ),
                    )
                ) ); ?>
            <div class="videos-list">
                <?php if ( $myposts->have_posts() ) : while ( $myposts->have_posts() ) : $myposts->the_post(); ?>
                    <?php get_template_part( 'template-parts/loop', 'standard' ); ?>
                <?php endwhile; endif; ?>
                <?php wp_reset_postdata(); ?>
            </div>
		</main><!-- #main -->
	</div><!-- #primary -->

<?php
get_sidebar();
get_footer();