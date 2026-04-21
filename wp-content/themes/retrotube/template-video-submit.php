<?php /* Template Name: Submit a Video */
$siteKey = xbox_get_field_value( 'wpst-options', 'recaptcha-site-key' );
$secret = xbox_get_field_value( 'wpst-options', 'recaptcha-secret-key' );
if(isset($_POST['wpst-submitted']) && isset($_POST['wpst-post_nonce_field']) && wp_verify_nonce($_POST['wpst-post_nonce_field'], 'post_nonce')) :
    if ( xbox_get_field_value( 'wpst-options', 'enable-recaptcha' ) == 'on' && $siteKey != '' && $secret != '' ) :
        if(isset($_POST['g-recaptcha-response']) && !empty($_POST['g-recaptcha-response'])) :

            $captcha = urlencode($_POST['g-recaptcha-response']);
            //$ip = $_SERVER['REMOTE_ADDR'];
            //get verify response data
            $verifyResponse = file_get_contents('https://www.google.com/recaptcha/api/siteverify?secret=' . $secret . '&response=' . $captcha);
            $responseData = json_decode($verifyResponse);

            if($responseData->success) :
                $post_information = array(
                    'post_title'    => esc_attr(strip_tags($_POST['wpst-video_title'])),
                    'post_content'  => esc_attr(strip_tags($_POST['wpst-video_description'])),
                    'post-type'     => 'post',
                    'post_status'   => 'pending',
                    'post_category' => array( $_POST['wpst-category_selected'] ),
                    'tax_input'     => array(
                        'post_tag'  => $_POST['wpst-tags'],
                        'actors'    => $_POST['wpst-actors']
                        )
                    );
                $post_id = wp_insert_post($post_information);

                if($post_id){
                    // Update Custom Meta
                    update_post_meta($post_id, 'video_url', esc_attr(strip_tags($_POST['wpst-video_url'])));
                    update_post_meta($post_id, 'embed', esc_attr($_POST['wpst-embed']));
                    update_post_meta($post_id, 'thumb', esc_attr(strip_tags($_POST['wpst-thumb'])));
                    if( ( isset($_POST['wpst-duration_hh']) ) && ( isset($_POST['wpst-duration_mm']) ) && ( isset($_POST['wpst-duration_ss']) ) ){
                        $duration_seconds = $_POST['wpst-duration_hh'] * 3600 + $_POST['wpst-duration_mm'] * 60 + $_POST['wpst-duration_ss'];
                        update_post_meta($post_id, 'duration', $duration_seconds);
                    }
                    set_post_format($post_id, 'video' );
                }

                $succMsg = esc_html__( 'Thanks for submitting a video! Your submission is being moderated.', 'wpst' ); ?>

                <?php else :
                    $errMsg = esc_html__( 'Captcha verification failed, please try again.', 'wpst' );
                endif; ?>

            <?php else:            
                $errMsg = esc_html__( 'Please click on the reCAPTCHA box.', 'wpst' );
            endif; ?>

        <?php else:
            $post_information = array(
                'post_title'    => esc_attr(strip_tags($_POST['wpst-video_title'])),
                'post_content'  => esc_attr(strip_tags($_POST['wpst-video_description'])),
                'post-type'     => 'post',
                'post_status'   => 'pending',
                'post_category' => array( $_POST['wpst-category_selected'] ),
                'tax_input'     => array(
                    'post_tag'  => $_POST['wpst-tags'],
                    'actors'    => $_POST['wpst-actors']
                    )
                );
            $post_id = wp_insert_post($post_information);
            
            if($post_id){
                // Update Custom Meta
                update_post_meta($post_id, 'video_url', esc_attr(strip_tags($_POST['wpst-video_url'])));
                update_post_meta($post_id, 'embed', esc_attr($_POST['wpst-embed']));
                update_post_meta($post_id, 'thumb', esc_attr(strip_tags($_POST['wpst-thumb'])));
                if( ( isset($_POST['wpst-duration_hh']) ) && ( isset($_POST['wpst-duration_mm']) ) && ( isset($_POST['wpst-duration_ss']) ) ){
                    $duration_seconds = $_POST['wpst-duration_hh'] * 3600 + $_POST['wpst-duration_mm'] * 60 + $_POST['wpst-duration_ss'];
                    update_post_meta($post_id, 'duration', $duration_seconds);
                }
                set_post_format($post_id, 'video' );
                $succMsg = esc_html__( 'Thanks for submitting a video! Your submission is being moderated.', 'wpst' );
            }
        endif; ?>

    <?php else:
        $errMsg = '';
        $succMsg = '';
    endif;
    
    get_header(); ?>

    <?php if( xbox_get_field_value( 'wpst-options', 'show-sidebar' ) == 'on' ) {
        if( xbox_get_field_value( 'wpst-options', 'sidebar-position' ) == 'sidebar-right' ) { $sidebar_pos = 'with-sidebar-right'; } else { $sidebar_pos = 'with-sidebar-left'; }
    }else{
        $sidebar_pos = '';
    } ?>

    <div id="primary" class="content-area <?php echo $sidebar_pos; ?> video-submit-area">
        <main id="main" class="site-main <?php echo $sidebar_pos; ?>" role="main">

            <?php if( xbox_get_field_value( 'wpst-options', 'enable-video-submission' ) == 'on' ) : ?>

                <header class="entry-header">
                    <?php the_title( '<h1 class="widget-title"><i class="fa fa-user"></i>', '</h1>' ); ?>
                </header>

                <?php if(!empty($errMsg)): ?><div class="alert alert-danger"><?php echo $errMsg; ?></div><?php endif; ?>
                <?php if(!empty($succMsg)): ?><div class="alert alert-success"><?php echo $succMsg; ?></div><?php endif; ?>
                
                <?php if (is_user_logged_in()) : ?>
                    <form data-abide action="" id="SubmitVideo" method="post">
                        <div id="html_element"></div>
                        <fieldset class="fieldset">
                            <legend><strong><?php esc_html_e( 'Video infos', 'wpst' ); ?></strong></legend>
                            <!-- Title -->
                            <label for="wpst-video_title"><?php esc_html_e('Title', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-title-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <input type="text" name="wpst-video_title" id="video_title" value="<?php if(isset($_POST['wpst-video_title'])) echo $_POST['wpst-video_title'];?>" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-title-required' ) == 'on' ) : ?>required="required"<?php endif; ?> />
                            
                            <!-- Description -->
                            <label for="wpst-video_description"><?php esc_html_e('Description', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-description-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <textarea name="wpst-video_description" id="video_description" rows="6" cols="30" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-description-required' ) == 'on' ) : ?>required="required"<?php endif; ?>><?php if(isset($_POST['wpst-video_description'])) { if(function_exists('stripslashes')) { echo stripslashes($_POST['wpst-video_description']); } else { echo $_POST['wpst-video_description']; } } ?></textarea>
                        </fieldset>
                        <fieldset class="fieldset">                           
                            <legend><strong><?php esc_html_e( 'Video type', 'wpst' ); ?></strong></legend>
                            <!-- Video URL -->
                            <label for="wpst-video_url"><?php esc_html_e('Video URL', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-video-link-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <input type="text" name="wpst-video_url" id="video_url" value="<?php if(isset($_POST['wpst-video_url'])) echo $_POST['wpst-video_url'];?>" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-video-link-required' ) == 'on' ) : ?>required="required"<?php endif; ?> />          
                           
                            <!-- Embed code -->               
                            <label for="wpst-embed"><?php esc_html_e('Iframe / Embed code', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-embed-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <textarea name="wpst-embed" id="embed" rows="4" cols="30" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-embed-required' ) == 'on' ) : ?>required="required"<?php endif; ?>><?php if(isset($_POST['wpst-embed'])) { if(function_exists('stripslashes')) { echo stripslashes($_POST['wpst-embed']); } else { echo $_POST['wpst-embed']; } } ?></textarea>
                        </fieldset>
                        <fieldset class="fieldset">
                            <legend><strong><?php esc_html_e( 'Video details', 'wpst' ); ?></strong></legend>
                            
                            <!-- Thumbnail URL -->
                            <label for="wpst-thumb"><?php esc_html_e('Thumbnail URL', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-thumbnail-link-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <input type="text" name="wpst-thumb" id="thumb" value="<?php if(isset($_POST['wpst-thumb'])) echo $_POST['wpst-thumb'];?>" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-thumbnail-link-required' ) == 'on' ) : ?>required="required"<?php endif; ?> />
                            
                            <!-- Category -->
                            <label for="wpst-category"><?php esc_html_e('Category', 'wpst') ?></label>
                            <select name="wpst-category_selected" data-width="auto">
                                <?php $categories = get_terms( 'category', array( 'hide_empty' => 0 ) );
                                foreach ( (array)$categories as $category ): ?>
                                    <option value="<?php echo $category->term_id; ?>"><?php echo $category->name;?></option>
                                <?php endforeach;?>
                            </select>

                            <!-- Tags -->
                            <label for="wpst-tags"><?php esc_html_e('Tags', 'wpst') ?> <small>(<?php esc_html_e('separated by commas', 'wpst') ?>)</small> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-tags-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <input type="text" name="wpst-tags" id="tags" value="<?php if(isset($_POST['wpst-tags'])) echo $_POST['wpst-tags'];?>" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-tags-required' ) == 'on' ) : ?>required="required"<?php endif; ?> />

                            <!-- Actors -->
                            <label for="wpst-actors"><?php esc_html_e('Actors', 'wpst') ?> <small>(<?php esc_html_e('separated by commas', 'wpst') ?>)</small> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-actors-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <input type="text" name="wpst-actors" id="actors" value="<?php if(isset($_POST['wpst-actors'])) echo $_POST['wpst-actors'];?>" <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-actors-required' ) == 'on' ) : ?>required="required"<?php endif; ?> />

                            <!-- Duration -->
                            <label class="margin-bottom-1" for="wpst-video_duration"><?php esc_html_e('Duration', 'wpst') ?> <?php if( xbox_get_field_value( 'wpst-options', 'video-submit-duration-required' ) == 'on' ) : ?><span class="required">*</span><?php endif; ?></label>
                            <?php
                                $hh = '';
                                $mm = '';
                                $ss = '';

                            if( get_post_meta($post->ID, 'duration', true) != '' ){
                                $duration = get_post_meta($post->ID, 'duration', true);
                                $hh = date( "H", $duration);
                                $mm = date( "i", $duration);
                                $ss = date( "s", $duration);
                            } ?>
                            <div id="video-duration-select">
                                <div class="duration-col">
                                    <span class="input-group-label"><?php esc_html_e( 'hour', 'wpst' ); ?></span>
                                    <select name="wpst-duration_hh">
                                        <option <?php if ($hh == "00") echo ' selected="selected"';?> value="00">00</option>
                                        <option <?php if ($hh == "01") echo ' selected="selected"';?> value="01">01</option>
                                        <option <?php if ($hh == "02") echo ' selected="selected"';?> value="02">02</option>
                                        <option <?php if ($hh == "03") echo ' selected="selected"';?> value="03">03</option>
                                        <option <?php if ($hh == "04") echo ' selected="selected"';?> value="04">04</option>
                                        <option <?php if ($hh == "05") echo ' selected="selected"';?> value="05">05</option>
                                        <option <?php if ($hh == "06") echo ' selected="selected"';?> value="06">06</option>
                                        <option <?php if ($hh == "07") echo ' selected="selected"';?> value="07">07</option>
                                        <option <?php if ($hh == "08") echo ' selected="selected"';?> value="08">08</option>
                                        <option <?php if ($hh == "09") echo ' selected="selected"';?> value="09">09</option>
                                        <option <?php if ($hh == "10") echo ' selected="selected"';?> value="10">10</option>
                                    </select>
                                </div>
                                <div class="duration-col">
                                    <span class="input-group-label"><?php esc_html_e( 'min', 'wpst' ); ?></span>
                                    <select name="wpst-duration_mm">
                                        <option <?php if ($mm == "00") echo ' selected="selected"';?> value="00">00</option>
                                        <option <?php if ($mm == "01") echo ' selected="selected"';?> value="01">01</option>
                                        <option <?php if ($mm == "02") echo ' selected="selected"';?> value="02">02</option>
                                        <option <?php if ($mm == "03") echo ' selected="selected"';?> value="03">03</option>
                                        <option <?php if ($mm == "04") echo ' selected="selected"';?> value="04">04</option>
                                        <option <?php if ($mm == "05") echo ' selected="selected"';?> value="05">05</option>
                                        <option <?php if ($mm == "06") echo ' selected="selected"';?> value="06">06</option>
                                        <option <?php if ($mm == "07") echo ' selected="selected"';?> value="07">07</option>
                                        <option <?php if ($mm == "08") echo ' selected="selected"';?> value="08">08</option>
                                        <option <?php if ($mm == "09") echo ' selected="selected"';?> value="09">09</option>
                                        <option <?php if ($mm == "10") echo ' selected="selected"';?> value="10">10</option>
                                        <option <?php if ($mm == "11") echo ' selected="selected"';?> value="11">11</option>
                                        <option <?php if ($mm == "12") echo ' selected="selected"';?> value="12">12</option>
                                        <option <?php if ($mm == "13") echo ' selected="selected"';?> value="13">13</option>
                                        <option <?php if ($mm == "14") echo ' selected="selected"';?> value="14">14</option>
                                        <option <?php if ($mm == "15") echo ' selected="selected"';?> value="15">15</option>
                                        <option <?php if ($mm == "16") echo ' selected="selected"';?> value="16">16</option>
                                        <option <?php if ($mm == "17") echo ' selected="selected"';?> value="17">17</option>
                                        <option <?php if ($mm == "18") echo ' selected="selected"';?> value="18">18</option>
                                        <option <?php if ($mm == "19") echo ' selected="selected"';?> value="19">19</option>
                                        <option <?php if ($mm == "20") echo ' selected="selected"';?> value="20">20</option>
                                        <option <?php if ($mm == "21") echo ' selected="selected"';?> value="21">21</option>
                                        <option <?php if ($mm == "22") echo ' selected="selected"';?> value="22">22</option>
                                        <option <?php if ($mm == "23") echo ' selected="selected"';?> value="23">23</option>
                                        <option <?php if ($mm == "24") echo ' selected="selected"';?> value="24">24</option>
                                        <option <?php if ($mm == "25") echo ' selected="selected"';?> value="25">25</option>
                                        <option <?php if ($mm == "26") echo ' selected="selected"';?> value="26">26</option>
                                        <option <?php if ($mm == "27") echo ' selected="selected"';?> value="27">27</option>
                                        <option <?php if ($mm == "28") echo ' selected="selected"';?> value="28">28</option>
                                        <option <?php if ($mm == "29") echo ' selected="selected"';?> value="29">29</option>
                                        <option <?php if ($mm == "30") echo ' selected="selected"';?> value="30">30</option>
                                        <option <?php if ($mm == "31") echo ' selected="selected"';?> value="31">31</option>
                                        <option <?php if ($mm == "32") echo ' selected="selected"';?> value="32">32</option>
                                        <option <?php if ($mm == "33") echo ' selected="selected"';?> value="33">33</option>
                                        <option <?php if ($mm == "34") echo ' selected="selected"';?> value="34">34</option>
                                        <option <?php if ($mm == "35") echo ' selected="selected"';?> value="35">35</option>
                                        <option <?php if ($mm == "36") echo ' selected="selected"';?> value="36">36</option>
                                        <option <?php if ($mm == "37") echo ' selected="selected"';?> value="37">37</option>
                                        <option <?php if ($mm == "38") echo ' selected="selected"';?> value="38">38</option>
                                        <option <?php if ($mm == "39") echo ' selected="selected"';?> value="39">39</option>
                                        <option <?php if ($mm == "40") echo ' selected="selected"';?> value="40">40</option>
                                        <option <?php if ($mm == "41") echo ' selected="selected"';?> value="41">41</option>
                                        <option <?php if ($mm == "42") echo ' selected="selected"';?> value="42">42</option>
                                        <option <?php if ($mm == "43") echo ' selected="selected"';?> value="43">43</option>
                                        <option <?php if ($mm == "44") echo ' selected="selected"';?> value="44">44</option>
                                        <option <?php if ($mm == "45") echo ' selected="selected"';?> value="45">45</option>
                                        <option <?php if ($mm == "46") echo ' selected="selected"';?> value="46">46</option>
                                        <option <?php if ($mm == "47") echo ' selected="selected"';?> value="47">47</option>
                                        <option <?php if ($mm == "48") echo ' selected="selected"';?> value="48">48</option>
                                        <option <?php if ($mm == "49") echo ' selected="selected"';?> value="49">49</option>
                                        <option <?php if ($mm == "50") echo ' selected="selected"';?> value="50">50</option>
                                        <option <?php if ($mm == "51") echo ' selected="selected"';?> value="51">51</option>
                                        <option <?php if ($mm == "52") echo ' selected="selected"';?> value="52">52</option>
                                        <option <?php if ($mm == "53") echo ' selected="selected"';?> value="53">53</option>
                                        <option <?php if ($mm == "54") echo ' selected="selected"';?> value="54">54</option>
                                        <option <?php if ($mm == "55") echo ' selected="selected"';?> value="55">55</option>
                                        <option <?php if ($mm == "56") echo ' selected="selected"';?> value="56">56</option>
                                        <option <?php if ($mm == "57") echo ' selected="selected"';?> value="57">57</option>
                                        <option <?php if ($mm == "58") echo ' selected="selected"';?> value="58">58</option>
                                        <option <?php if ($mm == "59") echo ' selected="selected"';?> value="59">59</option>
                                    </select>
                                </div>
                                <div class="duration-col">
                                    <span class="input-group-label"><?php esc_html_e( 'sec', 'wpst' ); ?></span>
                                    <select name="wpst-duration_ss">
                                        <option <?php if ($ss == "00") echo ' selected="selected"';?> value="00">00</option>
                                        <option <?php if ($ss == "01") echo ' selected="selected"';?> value="01">01</option>
                                        <option <?php if ($ss == "02") echo ' selected="selected"';?> value="02">02</option>
                                        <option <?php if ($ss == "03") echo ' selected="selected"';?> value="03">03</option>
                                        <option <?php if ($ss == "04") echo ' selected="selected"';?> value="04">04</option>
                                        <option <?php if ($ss == "05") echo ' selected="selected"';?> value="05">05</option>
                                        <option <?php if ($ss == "06") echo ' selected="selected"';?> value="06">06</option>
                                        <option <?php if ($ss == "07") echo ' selected="selected"';?> value="07">07</option>
                                        <option <?php if ($ss == "08") echo ' selected="selected"';?> value="08">08</option>
                                        <option <?php if ($ss == "09") echo ' selected="selected"';?> value="09">09</option>
                                        <option <?php if ($ss == "10") echo ' selected="selected"';?> value="10">10</option>
                                        <option <?php if ($ss == "11") echo ' selected="selected"';?> value="11">11</option>
                                        <option <?php if ($ss == "12") echo ' selected="selected"';?> value="12">12</option>
                                        <option <?php if ($ss == "13") echo ' selected="selected"';?> value="13">13</option>
                                        <option <?php if ($ss == "14") echo ' selected="selected"';?> value="14">14</option>
                                        <option <?php if ($ss == "15") echo ' selected="selected"';?> value="15">15</option>
                                        <option <?php if ($ss == "16") echo ' selected="selected"';?> value="16">16</option>
                                        <option <?php if ($ss == "17") echo ' selected="selected"';?> value="17">17</option>
                                        <option <?php if ($ss == "18") echo ' selected="selected"';?> value="18">18</option>
                                        <option <?php if ($ss == "19") echo ' selected="selected"';?> value="19">19</option>
                                        <option <?php if ($ss == "20") echo ' selected="selected"';?> value="20">20</option>
                                        <option <?php if ($ss == "21") echo ' selected="selected"';?> value="21">21</option>
                                        <option <?php if ($ss == "22") echo ' selected="selected"';?> value="22">22</option>
                                        <option <?php if ($ss == "23") echo ' selected="selected"';?> value="23">23</option>
                                        <option <?php if ($ss == "24") echo ' selected="selected"';?> value="24">24</option>
                                        <option <?php if ($ss == "25") echo ' selected="selected"';?> value="25">25</option>
                                        <option <?php if ($ss == "26") echo ' selected="selected"';?> value="26">26</option>
                                        <option <?php if ($ss == "27") echo ' selected="selected"';?> value="27">27</option>
                                        <option <?php if ($ss == "28") echo ' selected="selected"';?> value="28">28</option>
                                        <option <?php if ($ss == "29") echo ' selected="selected"';?> value="29">29</option>
                                        <option <?php if ($ss == "30") echo ' selected="selected"';?> value="30">30</option>
                                        <option <?php if ($ss == "31") echo ' selected="selected"';?> value="31">31</option>
                                        <option <?php if ($ss == "32") echo ' selected="selected"';?> value="32">32</option>
                                        <option <?php if ($ss == "33") echo ' selected="selected"';?> value="33">33</option>
                                        <option <?php if ($ss == "34") echo ' selected="selected"';?> value="34">34</option>
                                        <option <?php if ($ss == "35") echo ' selected="selected"';?> value="35">35</option>
                                        <option <?php if ($ss == "36") echo ' selected="selected"';?> value="36">36</option>
                                        <option <?php if ($ss == "37") echo ' selected="selected"';?> value="37">37</option>
                                        <option <?php if ($ss == "38") echo ' selected="selected"';?> value="38">38</option>
                                        <option <?php if ($ss == "39") echo ' selected="selected"';?> value="39">39</option>
                                        <option <?php if ($ss == "40") echo ' selected="selected"';?> value="40">40</option>
                                        <option <?php if ($ss == "41") echo ' selected="selected"';?> value="41">41</option>
                                        <option <?php if ($ss == "42") echo ' selected="selected"';?> value="42">42</option>
                                        <option <?php if ($ss == "43") echo ' selected="selected"';?> value="43">43</option>
                                        <option <?php if ($ss == "44") echo ' selected="selected"';?> value="44">44</option>
                                        <option <?php if ($ss == "45") echo ' selected="selected"';?> value="45">45</option>
                                        <option <?php if ($ss == "46") echo ' selected="selected"';?> value="46">46</option>
                                        <option <?php if ($ss == "47") echo ' selected="selected"';?> value="47">47</option>
                                        <option <?php if ($ss == "48") echo ' selected="selected"';?> value="48">48</option>
                                        <option <?php if ($ss == "49") echo ' selected="selected"';?> value="49">49</option>
                                        <option <?php if ($ss == "50") echo ' selected="selected"';?> value="50">50</option>
                                        <option <?php if ($ss == "51") echo ' selected="selected"';?> value="51">51</option>
                                        <option <?php if ($ss == "52") echo ' selected="selected"';?> value="52">52</option>
                                        <option <?php if ($ss == "53") echo ' selected="selected"';?> value="53">53</option>
                                        <option <?php if ($ss == "54") echo ' selected="selected"';?> value="54">54</option>
                                        <option <?php if ($ss == "55") echo ' selected="selected"';?> value="55">55</option>
                                        <option <?php if ($ss == "56") echo ' selected="selected"';?> value="56">56</option>
                                        <option <?php if ($ss == "57") echo ' selected="selected"';?> value="57">57</option>
                                        <option <?php if ($ss == "58") echo ' selected="selected"';?> value="58">58</option>
                                        <option <?php if ($ss == "59") echo ' selected="selected"';?> value="59">59</option>
                                    </select>
                                </div>
                            </div>
                        </fieldset>
                        
                        <?php wp_nonce_field('post_nonce', 'wpst-post_nonce_field'); ?>
                        <?php if ( xbox_get_field_value( 'wpst-options', 'enable-recaptcha' ) == 'on' && $siteKey != '' && $secret != '' ) : ?>
                            <div class="g-recaptcha" data-sitekey="<?php echo $siteKey; ?>" data-theme="dark"></div>
                        <?php endif; ?>
                        <?php /*<script src="https://www.google.com/recaptcha/api.js" async defer></script>
                        */ ?>
                        <input type="hidden" name="wpst-submitted" id="submitted" value="true" />
                        <?php echo apply_filters('update_button', '<button class="large" type="submit">' . __('Submit a video', 'wpst') . '</button>', 'submit_video' ); ?>                    
                    </form>
                <?php else : ?>
                    <div class="alert alert-info"><?php printf(__('You must be logged to submit a video. Please <a href="%s">login</a> or <a href="%s">register</a> a new account.', 'wpst'), '#wpst-login', '#wpst-register'); ?></div>
                <?php endif; ?>

            <?php else : ?>                
                <div class="alert alert-info"><?php esc_html_e('Video submission is disabled.', 'wpst'); ?></div>
            <?php endif; ?>

        </main><!-- #main -->
    </div><!-- #primary -->
            
<?php
get_sidebar();
get_footer();