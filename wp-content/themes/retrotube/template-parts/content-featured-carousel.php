<?php
if ( /*!is_active_sidebar( 'sidebar' ) ||*/ wp_is_mobile() && xbox_get_field_value( 'wpst-options', 'show-videos-carousel-mobile' ) == 'off' ) {
	return;
} ?>

<?php if( is_home() && xbox_get_field_value( 'wpst-options', 'show-videos-carousel' ) == 'on' ) : ?>
    <?php $the_query = new WP_Query( array(
		'posts_per_page' 	=> xbox_get_field_value( 'wpst-options', 'videos-carousel-amount' ),
		'meta_key'			=> 'featured_video',
		'meta_value'		=> 'on'
    )); ?>
    
	<?php if ( $the_query->have_posts() ) : ?>
		<div class="featured-carousel">
		<?php while ( $the_query->have_posts() ) : $the_query->the_post(); ?>

			<?php $trailer_url = get_post_meta($post->ID, 'trailer_url', true);
			$thumb_url = get_post_meta($post->ID, 'thumb', true); ?>

			<div class="slide">

				<?php if( $trailer_url != '' && !wp_is_mobile() ) : ?>

					<?php 
						if ( get_the_post_thumbnail() != '' ) {				
							$poster_url = get_the_post_thumbnail_url($post->ID, xbox_get_field_value( 'wpst-options', 'main-thumbnail-quality' ));
						}elseif( $thumb_url != '' ){
							$poster_url = $thumb_url;
						}
					?>

					<a class="video-with-trailer" href="<?php the_permalink(); ?>" title="<?php the_title(); ?>">
						<video class="wpst-trailer" width="100%" height="auto" preload="auto" muted loop poster="<?php echo $poster_url; ?>">
							<source src="<?php echo $trailer_url; ?>" type='video/mp4;' />
						</video>
						<?php if(get_post_meta($post->ID, 'hd_video', true) == 'on') : ?><span class="hd-video"><?php esc_html_e('HD', 'wpst'); ?></span><?php endif; ?>						
					</a>

				<?php else : ?>

					<a class="<?php if( xbox_get_field_value( 'wpst-options', 'enable-thumbnails-rotation' ) == 'on' ) : ?>thumbs-rotation<?php endif; ?>" <?php if( xbox_get_field_value( 'wpst-options', 'enable-thumbnails-rotation' ) == 'on' ) : ?>data-thumbs='<?php echo wpst_get_multithumbs($post->ID);?>'<?php endif; ?> href="<?php the_permalink(); ?>" title="<?php the_title(); ?>">
					<?php $thumb_url = get_post_meta($post->ID, 'thumb', true);
					if ( get_the_post_thumbnail() != '' ) {
						if( wp_is_mobile() ){
							echo '<img alt="' . get_the_title() . '" src="' . get_the_post_thumbnail_url($post->ID, 'wpst_thumb_medium') . '" title="' . get_the_title() . '">';
						}else{
							echo '<img alt="' . get_the_title() . '" data-src="' . get_the_post_thumbnail_url($post->ID, 'wpst_thumb_medium') . '" src="' . get_template_directory_uri() . '/assets/img/px.gif" title="' . get_the_title() . '">';
						}
					}elseif( $thumb_url != '' ){
						echo '<img data-src="' . $thumb_url . '" alt="' . get_the_title() . '" src="' . get_template_directory_uri() . '/assets/img/px.gif">';
					}else{
						echo '<div class="no-thumb"><span><i class="fa fa-image"></i> ' . esc_html__('No image', 'wpst') . '</span></div>';
					} ?>
					<?php if(get_post_meta($post->ID, 'hd_video', true) == 'on') : ?><span class="hd-video"><?php esc_html_e('HD', 'wpst'); ?></span><?php endif; ?></a>

				<?php endif; ?>

			</div><!-- .slide -->    

		<?php endwhile; ?>
		<?php wp_reset_postdata(); ?>
		</div>
		<script type="text/javascript">
			jQuery(document).ready(function() {
				jQuery('.featured-carousel').bxSlider({
					slideWidth: 320,
					maxSlides: 40,
					moveSlides: 1,
					pager: false,
					<?php if(xbox_get_field_value( 'wpst-options', 'videos-carousel-show-title' ) == 'on') : ?>
						captions: true,
					<?php endif; ?>
					<?php if(xbox_get_field_value( 'wpst-options', 'videos-carousel-auto-play' ) == 'on') : ?>
						auto: true,
						pause: 2000,
						autoHover: true,
					<?php endif; ?>			
					prevText: '',
					nextText: '',
					onSliderLoad: function(){
						jQuery(".featured-carousel").css("visibility", "visible");
					}        
				});
			});
		</script>
	<?php endif; ?>    
<?php endif; ?>
