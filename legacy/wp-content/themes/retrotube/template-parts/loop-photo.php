<?php 

$photos_list = get_post_gallery_images( $post->ID );
$photos_count = count($photos_list);

if($photos_count === 0){
	$photos_count = 1;
} ?>

<article id="post-<?php the_ID(); ?>" <?php if(xbox_get_field_value( 'wpst-options', 'videos-per-row-mobile' ) == '1') { post_class('thumb-block full-width'); }else{ post_class('thumb-block'); } ?>>
	<a href="<?php the_permalink(); ?>" title="<?php the_title(); ?>">
		<!-- Thumbnail -->
		<div class="post-thumbnail">			
			<?php 
			if ( get_the_post_thumbnail() != '' ) {				
				//the_post_thumbnail('wpst_thumb_small', array( 'alt' => get_the_title() ));
				if( wp_is_mobile() ){
					echo '<img src="' . get_the_post_thumbnail_url($post->ID, xbox_get_field_value( 'wpst-options', 'main-thumbnail-quality' )) . '" alt="' . get_the_title() . '">';
				}else{
					echo '<img data-src="' . get_the_post_thumbnail_url($post->ID, xbox_get_field_value( 'wpst-options', 'main-thumbnail-quality' )) . '" alt="' . get_the_title() . '" src="' . get_template_directory_uri() . '/assets/img/px.gif">';
				}
			}elseif(get_post_gallery()){
				echo '<div class="photo-bg" style="background: url(' . $photos_list[1] . ') no-repeat; background-size: cover;">';
			}elseif(get_the_content() != ''){
				echo get_first_image();
			}else{
				echo '<div class="no-thumb"><span><i class="fa fa-image"></i> ' . esc_html__('No image', 'wpst') . '</span></div>';
			} ?>

			<div class="photos-count">
				<i class="fa fa-camera"></i> <?php echo $photos_count; ?>
			</div>
        </div>
        
		<header class="entry-header">		
			<span><?php the_title(); ?></span>
		</header><!-- .entry-header -->
	</a>
</article><!-- #post-## -->
