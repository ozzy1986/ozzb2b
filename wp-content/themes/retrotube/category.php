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
					the_archive_title( '<h1 class="widget-title"><i class="fa fa-folder-open"></i>', '</h1>' );
					if(xbox_get_field_value( 'wpst-options', 'cat-desc-position' ) == 'top') { the_archive_description( '<div class="archive-description">', '</div>' ); }
				?>
				<?php get_template_part( 'template-parts/content', 'filters' ); ?>
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
		}		
		if(xbox_get_field_value( 'wpst-options', 'cat-desc-position' ) == 'bottom') : ?><div class="clear"></div><?php the_archive_description( '<div class="archive-description">', '</div>' ); ?><?php endif; ?>
		</main><!-- #main -->
	</div><!-- #primary -->
<?php
get_sidebar();
get_footer();