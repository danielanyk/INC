_base_ = [
    './_base_/models/cascade-rcnn_r50_fpn.py',
    './_base_/datasets/coco_detection.py',
    './_base_/schedules/schedule_1x.py', './_base_/default_runtime.py'
]
#https://www.kaggle.com/code/mlneo07/mmdetection-swin-transformer-fasterrcnn-training/notebook
# pretrained = 'https://github.com/SwinTransformer/storage/releases/download/v1.0.0/swin_small_patch4_window7_224.pth'

classes = ('raveling')  

pretrained = 'https://github.com/SwinTransformer/storage/releases/download/v1.0.0/swin_small_patch4_window7_224.pth'
model = dict(
    backbone=dict(
        _delete_=True,
        type='SwinTransformer',
        embed_dims=96,
        depths=[2, 2, 18, 2],
        num_heads=[3, 6, 12, 24],
        window_size=7,
        mlp_ratio=4,
        qkv_bias=True,
        qk_scale=None,
        drop_rate=0.,
        attn_drop_rate=0.,
        drop_path_rate=0.3,
        patch_norm=True,
        out_indices=(0, 1, 2, 3),
        with_cp=False,
        convert_weights=True,
        init_cfg=dict(type='Pretrained', checkpoint=pretrained)),
    neck=dict(in_channels=[96, 192, 384, 768]),
    roi_head=dict(
        type='CascadeRoIHead',
        num_stages=3,
        stage_loss_weights=[1, 0.5, 0.25],
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        bbox_head=[
            dict(
                type='Shared2FCBBoxHead',
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=len(classes),
                bbox_coder=dict(
                    type='DeltaXYWHBBoxCoder',
                    target_means=[0., 0., 0., 0.],
                    target_stds=[0.1, 0.1, 0.2, 0.2]),
                reg_class_agnostic=True,
                loss_cls=dict(
                    type='CrossEntropyLoss',
                    use_sigmoid=False,
                    loss_weight=1.0),
                reg_decoded_bbox=True,
                loss_bbox=dict(type='GIoULoss', loss_weight=10.0)),
            dict(
                type='Shared2FCBBoxHead',
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=len(classes),
                bbox_coder=dict(
                    type='DeltaXYWHBBoxCoder',
                    target_means=[0., 0., 0., 0.],
                    target_stds=[0.05, 0.05, 0.1, 0.1]),
                reg_class_agnostic=True,
                loss_cls=dict(
                    type='CrossEntropyLoss',
                    use_sigmoid=False,
                    loss_weight=1.0),
                reg_decoded_bbox=True,
                loss_bbox=dict(type='GIoULoss', loss_weight=10.0)),
            dict(
                type='Shared2FCBBoxHead',
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=len(classes),
                bbox_coder=dict(
                    type='DeltaXYWHBBoxCoder',
                    target_means=[0., 0., 0., 0.],
                    target_stds=[0.033, 0.033, 0.067, 0.067]),
                reg_class_agnostic=True,
                loss_cls=dict(
                    type='CrossEntropyLoss',
                    use_sigmoid=False,
                    loss_weight=1.0),
                reg_decoded_bbox=True,
                loss_bbox=dict(type='GIoULoss', loss_weight=10.0))
        ]))



optim_wrapper = dict(
    # _delete_=True,
    optimizer = dict(
        # _delete_=True,
        type='AdamW',
        lr=0.0001,
        betas=(0.9, 0.999),
        weight_decay=0.05,
        ) , 
         paramwise_cfg=dict(
            custom_keys={
                'absolute_pos_embed': dict(decay_mult=0.),
                'relative_position_bias_table': dict(decay_mult=0.),
                'norm': dict(decay_mult=0.)
        }))
# lr_config = dict(warmup_iters=500, step=[8, 11])
# runner = dict(max_epochs=14)

# load_from  = '/home/p2112675/mmdetection/work_dirs/faster_rcnn_swin/epoch_14.pth'


img_norm_cfg = dict( mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)

albu_train_transforms = [
    dict(
        type='ShiftScaleRotate',
        shift_limit=0.0625,
        scale_limit=0.0,
        rotate_limit=0,
        interpolation=1,
        p=0.5),
    dict( type = 'CLAHE' , p = 0.3),
    dict(type  = 'ColorJitter' , p = 0.3),
    dict(type  = 'FancyPCA' , p = 0.3),
    dict(type = 'GridDistortion' , p=0.3),
    dict(type = 'PiecewiseAffine' , p=0.3),
    dict(type = 'PixelDropout', p=0.3), 
    dict(type = 'ElasticTransform', p=0.3), 
    
    dict(
        type='RandomBrightnessContrast',
        brightness_limit=[0.1, 0.3],
        contrast_limit=[0.1, 0.3],
        p=0.9),
    dict(
        type='OneOf',
        transforms=[
            dict(
                type='RGBShift',
                r_shift_limit=10,
                g_shift_limit=10,
                b_shift_limit=10,
                p=1.0),
            dict(
                type='HueSaturationValue',
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=1.0)
        ],
        p=0.4),
    dict(type='JpegCompression', quality_lower=75, quality_upper=95, p=0.2),
    dict(type='ChannelShuffle', p=0.5),
    dict(
        type='OneOf',
        transforms=[
            dict(type='Blur', blur_limit=3, p=1.0),
            dict(type='MedianBlur', blur_limit=3, p=1.0)
        ],
        p=0.1)
]

train_pipeline = [
    dict(type='LoadImageFromFile',to_float32=True),
    dict(type='LoadAnnotations', with_bbox=True),
    
    
    dict(
        type='AutoAugment',
        policies=[[
            dict(
                type='Resize',
                img_scale=[(480, 1333), (512, 1333), (544, 1333), (576, 1333),
                           (608, 1333), (640, 1333), (672, 1333), (704, 1333),
                           (736, 1333), (768, 1333), (800, 1333)], # to-do
                multiscale_mode='value',
                keep_ratio=True)
        ],
                  [
                      dict(
                          type='Resize',
                          img_scale=[(400, 1333), (500, 1333), (600, 1333)],
                          multiscale_mode='value',
                          keep_ratio=True),
                      dict(
                          type='RandomCrop',
                          crop_type='absolute_range',
                          crop_size=(384, 600),
                          allow_negative_crop=True),
                      dict(
                          type='Resize',
                          img_scale=[(480, 1333), (512, 1333), (544, 1333),
                                     (576, 1333), (608, 1333), (640, 1333),
                                     (672, 1333), (704, 1333), (736, 1333),
                                     (768, 1333), (800, 1333)],
                          multiscale_mode='value',
                          override=True,
                          keep_ratio=True),
                      dict(
                            type='PhotoMetricDistortion',
                            brightness_delta=32,
                            contrast_range=(0.5, 1.5),
                            saturation_range=(0.5, 1.5),
                            hue_delta=18),
                    dict(
                            type='MinIoURandomCrop',
                            min_ious=(0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
                            min_crop_size=0.3),
                    dict(
                            type='CutOut',
                            n_holes=(5, 10),
                            cutout_shape=[(4, 4), (4, 8), (8, 4), (8, 8),
                                          (16, 32), (32, 16), (32, 32),
                                          (32, 48), (48, 32), (48, 48)]
                            )
                  ],
            dict(
        type='Albu',
            transforms=albu_train_transforms,
            bbox_params=dict(
                type='BboxParams',
                format='pascal_voc',
                label_fields=['gt_labels'],
                min_visibility=0.0,
                filter_lost_elements=True),
            keymap={
                'img': 'image',
                'gt_masks': 'masks',
                'gt_bboxes': 'bboxes'
            },
            update_pad_shape=False,
            skip_img_without_anno=True)
            
        
        ]),
    # dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1333, 800),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='DefaultFormatBundle'),
            dict(type='Collect', keys=['img'])
        ]),
    dict(type='PackDetInputs' , meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape' , 'scale_factor' ))


]

param_scheduler = [
    # dict(type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=1000),
    # dict(type='CosineRestartLR', periods = [1800,3600,7200] , restart_weights = [1,0.7,0.3] , eta_min = 0.000000000001)
        dict(type='CosineRestartLR', periods = [1556*10,1556*10,1556*5] , restart_weights = [1.0,0.8, 0.6] , eta_min = 0.00000005, 
             by_epoch=False, )
#     [1556*10,1556*10,1556*5]
]
train_cfg = dict(max_epochs=150 ,val_interval= 1 )



######################### data ################################

data_root ='/home/p2112589/fifnalexternal.v8i.coco/'
dataset_type = 'COCODataset'
# classes = ('single crack', 'transverse crack'  , 'pothole with crack' , 'alligator crack', 'block crack' , 'wearing course peeling off' ,'rigid pavement crack' , 'peeling off premix' , 'peel off with cracks' , 'multi crack', 'localise surface defect' , 'damaged base crack')
# classes = ('alligator crack', "block crack" ,"damaged base crack" ,"localise surface defect"  , \
#            "multi crack","peel off with cracks","peeling off premix","pothole with crack" ,"rigid pavement crack",\
#          "single crack" , "transverse crack"  ,  "wearing course peeling off")
metainfo = {
    'classes':classes, 
}


train_dataloader = dict(
    batch_size=4,
    num_workers=0, 
    persistent_workers = False,
    # _delete_ = True,
    # type = '',
    
    sampler = dict(type = 'ClassAwareSampler' , seed =228, _delete_ = True  ),

    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='train/_annotations.coco.json',
        data_prefix=dict(img='train/')))
val_dataloader = dict(
    num_workers=0, 
    persistent_workers = False,
    
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='valid/_annotations.coco.json',
        data_prefix=dict(img='valid/')))
test_dataloader=  dict(
    # _delete_ = True , 
    num_workers=0, 
    persistent_workers = False,
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file='test/_annotations.coco.json',
        data_prefix=dict(img='test/')))

val_evaluator = dict(
    # _delete_ = True, 
    type='CocoMetric',
    ann_file=data_root + '/valid/_annotations.coco.json',
    metric='bbox',
    format_only=False,
    backend_args=None)
test_evaluator = dict(
    # _delete_ = True, 
    type='CocoMetric',
    ann_file=data_root + '/test/_annotations.coco.json',
    metric='bbox',
    format_only=False,
    backend_args=None)


# log config
default_hooks = dict(logger=dict(interval=100))
fp16 = dict(loss_scale='dynamic')