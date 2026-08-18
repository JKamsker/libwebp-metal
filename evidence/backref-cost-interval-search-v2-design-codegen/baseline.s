	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 26, 0	sdk_version 26, 2
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; -- Begin function VP8LBackwardReferencesTraceBackwards
lCPI0_0:
	.byte	1                               ; 0x1
	.byte	2                               ; 0x2
	.byte	4                               ; 0x4
	.byte	8                               ; 0x8
	.byte	16                              ; 0x10
	.byte	32                              ; 0x20
	.byte	64                              ; 0x40
	.byte	128                             ; 0x80
	.byte	1                               ; 0x1
	.byte	2                               ; 0x2
	.byte	4                               ; 0x4
	.byte	8                               ; 0x8
	.byte	16                              ; 0x10
	.byte	32                              ; 0x20
	.byte	64                              ; 0x40
	.byte	128                             ; 0x80
lCPI0_1:
	.short	1                               ; 0x1
	.short	2                               ; 0x2
	.short	4                               ; 0x4
	.short	8                               ; 0x8
	.short	16                              ; 0x10
	.short	32                              ; 0x20
	.short	64                              ; 0x40
	.short	128                             ; 0x80
	.section	__TEXT,__literal8,8byte_literals
	.p2align	3, 0x0
lCPI0_2:
	.long	0                               ; 0x0
	.long	1                               ; 0x1
	.section	__TEXT,__text,regular,pure_instructions
	.globl	_VP8LBackwardReferencesTraceBackwards
	.p2align	2
_VP8LBackwardReferencesTraceBackwards:  ; @VP8LBackwardReferencesTraceBackwards
	.cfi_startproc
; %bb.0:
	sub	sp, sp, #240
	stp	x28, x27, [sp, #144]            ; 16-byte Folded Spill
	stp	x26, x25, [sp, #160]            ; 16-byte Folded Spill
	stp	x24, x23, [sp, #176]            ; 16-byte Folded Spill
	stp	x22, x21, [sp, #192]            ; 16-byte Folded Spill
	stp	x20, x19, [sp, #208]            ; 16-byte Folded Spill
	stp	x29, x30, [sp, #224]            ; 16-byte Folded Spill
	add	x29, sp, #224
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	mov	x27, x6
	mov	x20, x5
	stp	x4, x2, [sp, #104]              ; 16-byte Folded Spill
	mov	x21, x3
	mov	x23, x0
	mul	w8, w1, w0
	sxtw	x25, w8
	mov	x0, x25
	mov	w1, #2                          ; =0x2
	bl	_WebPSafeMalloc
	mov	x28, x0
	cbz	x0, LBB0_160
; %bb.1:
	mov	w8, #1                          ; =0x1
	lsl	w8, w8, w21
	add	w8, w8, #280
	mov	w9, #280                        ; =0x118
	cmp	w21, #1
	csel	w8, w9, w8, lt
	sbfiz	x8, x8, #2, #32
	add	x1, x8, #3240
	mov	w0, #1                          ; =0x1
	bl	_WebPSafeCalloc
	mov	x22, x0
	mov	w0, #1                          ; =0x1
	mov	w1, #33224                      ; =0x81c8
	bl	_WebPSafeCalloc
	mov	x26, x0
	cmp	x22, #0
	ccmp	x0, #0, #4, ne
	b.ne	LBB0_3
LBB0_2:
	mov	w19, #0                         ; =0x0
	b	LBB0_138
LBB0_3:
	add	x8, x22, #3240
	str	x8, [x22, #3232]
	cmp	w21, #1
	b.lt	LBB0_5
; %bb.4:
	sub	x0, x29, #96
	mov	x1, x21
	bl	_VP8LColorCacheInit
	cbz	w0, LBB0_2
LBB0_5:
	mov	x0, x21
	bl	_VP8LAllocateHistogram
	cbz	x0, LBB0_22
; %bb.6:
	mov	x24, x0
	mov	w19, #1                         ; =0x1
	mov	x1, x21
	mov	w2, #1                          ; =0x1
	bl	_VP8LHistogramInit
Lloh0:
	adrp	x1, _VP8LDistanceToPlaneCode@GOTPAGE
Lloh1:
	ldr	x1, [x1, _VP8LDistanceToPlaneCode@GOTPAGEOFF]
	str	x20, [sp, #16]                  ; 8-byte Folded Spill
	mov	x0, x20
	mov	x2, x23
	mov	x3, x24
	bl	_VP8LHistogramStoreRefs
	ldr	w8, [x24, #3240]
	lsl	w9, w19, w8
	add	w9, w9, #280
	mov	w10, #280                       ; =0x118
	cmp	w8, #0
	csel	w19, w9, w10, gt
	str	x22, [sp, #96]                  ; 8-byte Folded Spill
	ldr	x22, [x22, #3232]
	cmp	w19, #1
	str	w21, [sp, #76]                  ; 4-byte Folded Spill
	str	x25, [sp, #56]                  ; 8-byte Folded Spill
	str	w23, [sp, #36]                  ; 4-byte Folded Spill
	b.lt	LBB0_17
; %bb.7:
	ldr	x20, [x24]
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	and	x9, x19, #0x7ffffff0
	mov	x8, x9
	add	x10, x20, #32
	mov	x11, x9
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
LBB0_8:                                 ; =>This Inner Loop Header: Depth=1
	ldp	q16, q17, [x10, #-32]
	ldp	q18, q19, [x10], #64
	add.4s	v0, v16, v0
	add.4s	v1, v17, v1
	add.4s	v6, v18, v6
	add.4s	v7, v19, v7
	cmtst.4s	v16, v16, v16
	cmtst.4s	v17, v17, v17
	cmtst.4s	v18, v18, v18
	cmtst.4s	v19, v19, v19
	sub.4s	v2, v2, v16
	sub.4s	v3, v3, v17
	sub.4s	v4, v4, v18
	sub.4s	v5, v5, v19
	subs	x11, x11, #16
	b.ne	LBB0_8
; %bb.9:
	add.4s	v0, v1, v0
	add.4s	v0, v6, v0
	add.4s	v0, v7, v0
	addv.4s	s0, v0
	fmov	w0, s0
	add.4s	v1, v3, v2
	add.4s	v2, v5, v4
	add.4s	v1, v2, v1
	addv.4s	s2, v1
	fmov	w10, s2
	cmp	x9, x19
	b.eq	LBB0_16
; %bb.10:
	tst	x19, #0xc
	b.eq	LBB0_14
; %bb.11:
	and	x8, x19, #0x7ffffffc
	movi.2d	v1, #0000000000000000
	mov.s	v1[0], v0[0]
	movi.2d	v0, #0000000000000000
	mov.s	v0[0], v2[0]
	ubfx	x10, x19, #4, #27
	add	x10, x20, x10, lsl #6
	sub	x9, x8, x9
LBB0_12:                                ; =>This Inner Loop Header: Depth=1
	ldr	q2, [x10], #16
	add.4s	v1, v2, v1
	cmtst.4s	v2, v2, v2
	sub.4s	v0, v0, v2
	subs	x9, x9, #4
	b.ne	LBB0_12
; %bb.13:
	addv.4s	s1, v1
	fmov	w0, s1
	addv.4s	s0, v0
	fmov	w10, s0
	cmp	x8, x19
	b.eq	LBB0_16
LBB0_14:
	sub	x9, x19, x8
	add	x8, x20, x8, lsl #2
LBB0_15:                                ; =>This Inner Loop Header: Depth=1
	ldr	w11, [x8], #4
	add	w0, w11, w0
	cmp	w11, #0
	cinc	w10, w10, ne
	subs	x9, x9, #1
	b.ne	LBB0_15
LBB0_16:
	cmp	w10, #1
	b.hi	LBB0_25
LBB0_17:
	sbfiz	x1, x19, #2, #32
	mov	x0, x22
	bl	_bzero
LBB0_18:
	str	x28, [sp, #48]                  ; 8-byte Folded Spill
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	add	x28, x26, #8, lsl #12           ; =32768
	add	x20, x24, #3080
	add	x19, x24, #8
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB0_19:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x24, x8
	ldur	q16, [x9, #8]
	ldur	q17, [x9, #24]
	ldur	q18, [x9, #40]
	ldur	q19, [x9, #56]
	add.4s	v0, v16, v0
	add.4s	v1, v17, v1
	add.4s	v2, v18, v2
	add.4s	v3, v19, v3
	cmtst.4s	v16, v16, v16
	cmtst.4s	v17, v17, v17
	cmtst.4s	v18, v18, v18
	cmtst.4s	v19, v19, v19
	sub.4s	v4, v4, v16
	sub.4s	v5, v5, v17
	sub.4s	v6, v6, v18
	sub.4s	v7, v7, v19
	add	x8, x8, #64
	cmp	x8, #1024
	b.ne	LBB0_19
; %bb.20:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	add	x9, x9, #1024
	cmp	w8, #1
	str	x9, [sp, #88]                   ; 8-byte Folded Spill
	b.hi	LBB0_23
; %bb.21:
	mov	x0, x9
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB0_32
LBB0_22:
	bl	_VP8LFreeHistogram
	mov	w19, #0                         ; =0x0
	cmp	w21, #1
	b.ge	LBB0_137
	b	LBB0_138
LBB0_23:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
Lloh2:
	adrp	x22, _VP8LFastLog2Slow@GOTPAGE
Lloh3:
	ldr	x22, [x22, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh4:
	adrp	x23, _kLog2Table@GOTPAGE
Lloh5:
	ldr	x23, [x23, _kLog2Table@GOTPAGEOFF]
	cmp	w0, #255
	b.hi	LBB0_27
; %bb.24:
	ldr	w21, [x23, w0, uxtw #2]
	b	LBB0_28
LBB0_25:
	cmp	w0, #255
	b.hi	LBB0_83
; %bb.26:
Lloh6:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh7:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w21, [x8, w0, uxtw #2]
	b	LBB0_84
LBB0_27:
	ldr	x8, [x22]
	blr	x8
	ldr	x9, [sp, #88]                   ; 8-byte Folded Reload
	mov	x21, x0
LBB0_28:
	mov	x25, #0                         ; =0x0
	b	LBB0_30
LBB0_29:                                ;   in Loop: Header=BB0_30 Depth=1
	ldr	x8, [x22]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x9, [sp, #88]                   ; 8-byte Folded Reload
	sub	w8, w21, w0
	str	w8, [x9, x25]
	add	x25, x25, #4
	cmp	x25, #1024
	b.eq	LBB0_32
LBB0_30:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x25]
	cmp	w0, #255
	b.hi	LBB0_29
; %bb.31:                               ;   in Loop: Header=BB0_30 Depth=1
	ldr	w0, [x23, x0, lsl #2]
	sub	w8, w21, w0
	str	w8, [x9, x25]
	add	x25, x25, #4
	cmp	x25, #1024
	b.ne	LBB0_30
LBB0_32:
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	add	x19, x24, #1032
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB0_33:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x24, x8
	add	x10, x9, #1032
	add	x11, x9, #1048
	add	x12, x9, #1064
	add	x9, x9, #1080
	ldr	q16, [x10]
	ldr	q17, [x11]
	ldr	q18, [x12]
	ldr	q19, [x9]
	add.4s	v0, v16, v0
	add.4s	v1, v17, v1
	add.4s	v2, v18, v2
	add.4s	v3, v19, v3
	cmtst.4s	v16, v16, v16
	cmtst.4s	v17, v17, v17
	cmtst.4s	v18, v18, v18
	cmtst.4s	v19, v19, v19
	sub.4s	v4, v4, v16
	sub.4s	v5, v5, v17
	sub.4s	v6, v6, v18
	sub.4s	v7, v7, v19
	add	x8, x8, #64
	cmp	x8, #1024
	b.ne	LBB0_33
; %bb.34:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	add	x9, x9, #2048
	cmp	w8, #1
	str	x9, [sp, #80]                   ; 8-byte Folded Spill
	b.hi	LBB0_36
; %bb.35:
	mov	x0, x9
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB0_43
LBB0_36:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
	cmp	w0, #255
	b.hi	LBB0_38
; %bb.37:
Lloh8:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh9:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w21, [x8, w0, uxtw #2]
	b	LBB0_39
LBB0_38:
Lloh10:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh11:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh12:
	ldr	x8, [x8]
	blr	x8
	ldr	x9, [sp, #80]                   ; 8-byte Folded Reload
	mov	x21, x0
LBB0_39:
	mov	x22, #0                         ; =0x0
Lloh13:
	adrp	x23, _kLog2Table@GOTPAGE
Lloh14:
	ldr	x23, [x23, _kLog2Table@GOTPAGEOFF]
Lloh15:
	adrp	x25, _VP8LFastLog2Slow@GOTPAGE
Lloh16:
	ldr	x25, [x25, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB0_41
LBB0_40:                                ;   in Loop: Header=BB0_41 Depth=1
	ldr	x8, [x25]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x9, [sp, #80]                   ; 8-byte Folded Reload
	sub	w8, w21, w0
	str	w8, [x9, x22]
	add	x22, x22, #4
	cmp	x22, #1024
	b.eq	LBB0_43
LBB0_41:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x22]
	cmp	w0, #255
	b.hi	LBB0_40
; %bb.42:                               ;   in Loop: Header=BB0_41 Depth=1
	ldr	w0, [x23, x0, lsl #2]
	sub	w8, w21, w0
	str	w8, [x9, x22]
	add	x22, x22, #4
	cmp	x22, #1024
	b.ne	LBB0_41
LBB0_43:
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	add	x19, x24, #2056
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB0_44:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x24, x8
	add	x10, x9, #2056
	add	x11, x9, #2072
	add	x12, x9, #2088
	add	x9, x9, #2104
	ldr	q16, [x10]
	ldr	q17, [x11]
	ldr	q18, [x12]
	ldr	q19, [x9]
	add.4s	v0, v16, v0
	add.4s	v1, v17, v1
	add.4s	v2, v18, v2
	add.4s	v3, v19, v3
	cmtst.4s	v16, v16, v16
	cmtst.4s	v17, v17, v17
	cmtst.4s	v18, v18, v18
	cmtst.4s	v19, v19, v19
	sub.4s	v4, v4, v16
	sub.4s	v5, v5, v17
	sub.4s	v6, v6, v18
	sub.4s	v7, v7, v19
	add	x8, x8, #64
	cmp	x8, #1024
	b.ne	LBB0_44
; %bb.45:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	cmp	w8, #1
	ldr	x0, [sp, #96]                   ; 8-byte Folded Reload
	b.hi	LBB0_47
; %bb.46:
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB0_54
LBB0_47:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
	cmp	w0, #255
	b.hi	LBB0_49
; %bb.48:
Lloh17:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh18:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w21, [x8, w0, uxtw #2]
	b	LBB0_50
LBB0_49:
Lloh19:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh20:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh21:
	ldr	x8, [x8]
	blr	x8
	mov	x21, x0
LBB0_50:
	mov	x22, #0                         ; =0x0
Lloh22:
	adrp	x23, _kLog2Table@GOTPAGE
Lloh23:
	ldr	x23, [x23, _kLog2Table@GOTPAGEOFF]
Lloh24:
	adrp	x25, _VP8LFastLog2Slow@GOTPAGE
Lloh25:
	ldr	x25, [x25, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB0_52
LBB0_51:                                ;   in Loop: Header=BB0_52 Depth=1
	ldr	x8, [x25]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	sub	w8, w21, w0
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	str	w8, [x9, x22]
	add	x22, x22, #4
	cmp	x22, #1024
	b.eq	LBB0_54
LBB0_52:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x22]
	cmp	w0, #255
	b.hi	LBB0_51
; %bb.53:                               ;   in Loop: Header=BB0_52 Depth=1
	ldr	w0, [x23, x0, lsl #2]
	sub	w8, w21, w0
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	str	w8, [x9, x22]
	add	x22, x22, #4
	cmp	x22, #1024
	b.ne	LBB0_52
LBB0_54:
	ldp	q7, q6, [x20, #32]
	ldp	q5, q3, [x20, #64]
	ldp	q1, q0, [x20, #96]
	ldp	q17, q16, [x20]
	cmeq.4s	v2, v0, #0
	cmeq.4s	v4, v1, #0
	uzp1.8h	v2, v4, v2
	cmeq.4s	v4, v3, #0
	cmeq.4s	v18, v5, #0
	uzp1.8h	v4, v18, v4
	uzp1.16b	v2, v4, v2
Lloh26:
	adrp	x8, lCPI0_0@PAGE
Lloh27:
	ldr	q4, [x8, lCPI0_0@PAGEOFF]
	bic.16b	v2, v4, v2
	ext.16b	v18, v2, v2, #8
	zip1.16b	v2, v2, v18
	addv.8h	h2, v2
	fmov	w8, s2
	cmeq.4s	v2, v6, #0
	cmeq.4s	v18, v7, #0
	uzp1.8h	v2, v18, v2
	cmeq.4s	v18, v16, #0
	cmeq.4s	v19, v17, #0
	uzp1.8h	v18, v19, v18
	uzp1.16b	v2, v18, v2
	bic.16b	v2, v4, v2
	ext.16b	v4, v2, v2, #8
	zip1.16b	v2, v2, v4
	addv.8h	h2, v2
	fmov	w9, s2
	bfi	w9, w8, #16, #16
	ldp	q4, q2, [x20, #128]
	cmeq.4s	v18, v2, #0
	cmeq.4s	v19, v4, #0
	uzp1.8h	v18, v19, v18
Lloh28:
	adrp	x8, lCPI0_1@PAGE
Lloh29:
	ldr	q19, [x8, lCPI0_1@PAGEOFF]
	bic.16b	v18, v19, v18
	addv.8h	h18, v18
	fmov	w8, s18
	and	w8, w8, #0xff
	fmov	s18, w9
	cnt.8b	v18, v18
	uaddlv.8b	h18, v18
	fmov	w9, s18
	fmov	s18, w8
	cnt.8b	v18, v18
	uaddlv.8b	h18, v18
	fmov	w8, s18
	add	w8, w9, w8
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	add	x13, x9, #3072
	cmp	w8, #1
	str	x13, [sp, #64]                  ; 8-byte Folded Spill
	b.hi	LBB0_56
; %bb.55:
	movi.2d	v0, #0000000000000000
	stp	q0, q0, [x13, #128]
	stp	q0, q0, [x13, #96]
	stp	q0, q0, [x13, #64]
	stp	q0, q0, [x13, #32]
	stp	q0, q0, [x13]
	ldr	x25, [sp, #56]                  ; 8-byte Folded Reload
	b	LBB0_63
LBB0_56:
	mov.s	w8, v17[1]
	fmov	w9, s17
	add	w8, w8, w9
	mov.s	w9, v17[2]
	mov.s	w10, v17[3]
	add	w9, w9, w10
	add	w8, w8, w9
	mov.s	w9, v16[1]
	mov.s	w10, v16[2]
	fmov	w11, s16
	add	w9, w11, w9
	add	w9, w9, w10
	add	w8, w8, w9
	mov.s	w9, v16[3]
	fmov	w10, s7
	mov.s	w11, v7[1]
	mov.s	w12, v7[2]
	add	w9, w9, w10
	add	w9, w9, w11
	add	w9, w9, w12
	add	w8, w8, w9
	mov.s	w9, v7[3]
	fmov	w10, s6
	mov.s	w11, v6[1]
	add	w9, w9, w10
	add	w9, w9, w11
	mov.s	w10, v6[2]
	mov.s	w11, v6[3]
	add	w9, w9, w10
	add	w9, w9, w11
	add	w8, w8, w9
	fmov	w9, s5
	mov.s	w10, v5[1]
	mov.s	w11, v5[2]
	add	w9, w9, w10
	add	w9, w9, w11
	mov.s	w10, v5[3]
	fmov	w11, s3
	mov.s	w12, v3[1]
	add	w9, w9, w10
	add	w9, w9, w11
	mov.s	w10, v3[2]
	mov.s	w11, v3[3]
	add	w9, w9, w12
	add	w8, w8, w9
	fmov	w9, s1
	add	w10, w10, w11
	add	w9, w10, w9
	mov.s	w10, v1[1]
	mov.s	w11, v1[2]
	add	w9, w9, w10
	add	w9, w9, w11
	mov.s	w10, v1[3]
	fmov	w11, s0
	add	w9, w9, w10
	add	w9, w9, w11
	add	w8, w8, w9
	mov.s	w9, v0[1]
	mov.s	w10, v0[2]
	mov.s	w11, v0[3]
	add	w9, w9, w10
	add	w9, w9, w11
	fmov	w10, s4
	mov.s	w11, v4[1]
	mov.s	w12, v4[2]
	add	w9, w9, w10
	add	w9, w9, w11
	mov.s	w10, v4[3]
	add	w9, w9, w12
	add	w9, w9, w10
	fmov	w10, s2
	add	w9, w9, w10
	add	w8, w8, w9
	mov.s	w9, v2[1]
	mov.s	w10, v2[2]
	mov.s	w11, v2[3]
	add	w9, w9, w10
	add	w9, w9, w11
	add	w0, w8, w9
	cmp	w0, #255
	ldr	x25, [sp, #56]                  ; 8-byte Folded Reload
	b.hi	LBB0_58
; %bb.57:
Lloh30:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh31:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w21, [x8, w0, uxtw #2]
	b	LBB0_59
LBB0_58:
Lloh32:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh33:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh34:
	ldr	x8, [x8]
	blr	x8
	ldr	x13, [sp, #64]                  ; 8-byte Folded Reload
	mov	x21, x0
LBB0_59:
	mov	x19, #0                         ; =0x0
Lloh35:
	adrp	x22, _kLog2Table@GOTPAGE
Lloh36:
	ldr	x22, [x22, _kLog2Table@GOTPAGEOFF]
Lloh37:
	adrp	x23, _VP8LFastLog2Slow@GOTPAGE
Lloh38:
	ldr	x23, [x23, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB0_61
LBB0_60:                                ;   in Loop: Header=BB0_61 Depth=1
	ldr	x8, [x23]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x13, [sp, #64]                  ; 8-byte Folded Reload
	sub	w8, w21, w0
	str	w8, [x13, x19]
	add	x19, x19, #4
	cmp	x19, #160
	b.eq	LBB0_63
LBB0_61:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x20, x19]
	cmp	w0, #255
	b.hi	LBB0_60
; %bb.62:                               ;   in Loop: Header=BB0_61 Depth=1
	ldr	w0, [x22, x0, lsl #2]
	sub	w8, w21, w0
	str	w8, [x13, x19]
	add	x19, x19, #4
	cmp	x19, #160
	b.ne	LBB0_61
LBB0_63:
	mov	x0, x24
	bl	_VP8LFreeHistogram
	mov	w8, #4095                       ; =0xfff
	str	xzr, [x26, #16]
	cmp	w25, #4095
	csel	w19, w25, w8, lt
	str	xzr, [x26]
	str	xzr, [x28, #448]
	str	wzr, [x26, #8]
	ldr	x8, [sp, #48]                   ; 8-byte Folded Reload
	stp	xzr, x8, [x28, #24]
	mov	w8, #32808                      ; =0x8028
	add	x9, x26, x8
	str	x9, [sp, #40]                   ; 8-byte Folded Spill
	str	xzr, [x28, #72]
	mov	w8, #32848                      ; =0x8050
	add	x8, x26, x8
	str	x9, [x28, #112]
	mov	w9, #32888                      ; =0x8078
	add	x9, x26, x9
	str	x8, [x28, #152]
	mov	w8, #32928                      ; =0x80a0
	add	x8, x26, x8
	str	x9, [x28, #192]
	mov	w9, #32968                      ; =0x80c8
	add	x9, x26, x9
	str	x8, [x28, #232]
	mov	w8, #33008                      ; =0x80f0
	add	x8, x26, x8
	str	x9, [x28, #272]
	mov	w9, #33048                      ; =0x8118
	add	x9, x26, x9
	str	x8, [x28, #312]
	mov	w8, #33088                      ; =0x8140
	add	x8, x26, x8
	str	x9, [x28, #352]
	mov	w9, #33128                      ; =0x8168
	add	x9, x26, x9
	str	x8, [x28, #392]
	mov	w8, #33168                      ; =0x8190
	add	x20, x26, x8
	stp	x9, x20, [x28, #432]
	cmp	w25, #0
	b.le	LBB0_71
; %bb.64:
	mov	x9, #0                          ; =0x0
	ldr	x22, [sp, #96]                  ; 8-byte Folded Reload
	ldr	x8, [x22, #3232]
	add	x10, x8, #1024
	add	x8, x26, #32
Lloh39:
	adrp	x11, _kPrefixEncodeCode@GOTPAGE
Lloh40:
	ldr	x11, [x11, _kPrefixEncodeCode@GOTPAGEOFF]
	add	x11, x11, #1
	b	LBB0_67
LBB0_65:                                ;   in Loop: Header=BB0_67 Depth=1
	sub	w13, w9, #1
	clz	w12, w13
	eor	w14, w12, #0x1f
	sub	w12, w14, #1
	lsr	w13, w13, w12
	and	w13, w13, #0x1
	orr	w13, w13, w14, lsl #1
LBB0_66:                                ;   in Loop: Header=BB0_67 Depth=1
	ldr	w13, [x10, w13, sxtw #2]
	sxtw	x12, w12
	add	x12, x13, x12, lsl #23
	str	x12, [x8, x9, lsl #3]
	add	x9, x9, #1
	add	x11, x11, #2
	cmp	x19, x9
	b.eq	LBB0_69
LBB0_67:                                ; =>This Inner Loop Header: Depth=1
	cmp	x9, #511
	b.hi	LBB0_65
; %bb.68:                               ;   in Loop: Header=BB0_67 Depth=1
	ldursb	w13, [x11, #-1]
	ldrsb	w12, [x11]
	b	LBB0_66
LBB0_69:
	mov	w0, #1                          ; =0x1
	str	x0, [x26, #24]
	cmp	w25, #1
	b.ne	LBB0_72
; %bb.70:
	mov	w21, #0                         ; =0x0
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x26, #16]
	cbnz	x0, LBB0_80
	b	LBB0_136
LBB0_71:
	mov	w21, #0                         ; =0x0
	mov	w0, #1                          ; =0x1
	str	x0, [x26, #24]
	ldr	x22, [sp, #96]                  ; 8-byte Folded Reload
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x26, #16]
	cbnz	x0, LBB0_80
	b	LBB0_136
LBB0_72:
	ldr	x12, [x8]
	sub	x9, x19, #1
	sub	x10, x19, #2
	and	x8, x9, #0x7
	cmp	x10, #7
	b.hs	LBB0_88
; %bb.73:
	mov	w0, #1                          ; =0x1
	mov	w10, #1                         ; =0x1
LBB0_74:
	cbz	x8, LBB0_79
; %bb.75:
	add	x9, x26, x10, lsl #3
	add	x9, x9, #32
	b	LBB0_77
LBB0_76:                                ;   in Loop: Header=BB0_77 Depth=1
	mov	x12, x10
	subs	x8, x8, #1
	b.eq	LBB0_79
LBB0_77:                                ; =>This Inner Loop Header: Depth=1
	ldr	x10, [x9], #8
	cmp	x10, x12
	b.eq	LBB0_76
; %bb.78:                               ;   in Loop: Header=BB0_77 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	b	LBB0_76
LBB0_79:
	mov	w21, #1                         ; =0x1
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x26, #16]
	cbz	x0, LBB0_136
LBB0_80:
Lloh41:
	adrp	x8, lCPI0_2@PAGE
Lloh42:
	ldr	d0, [x8, lCPI0_2@PAGEOFF]
	str	d0, [x0, #8]
	mov	x8, x26
	ldr	x13, [x8, #32]!
	str	x13, [x0]
	cbz	w21, LBB0_126
; %bb.81:
	sub	x11, x19, #1
	sub	x10, x19, #2
	and	x9, x11, #0x7
	cmp	x10, #7
	b.hs	LBB0_106
; %bb.82:
	mov	w10, #1                         ; =0x1
	b	LBB0_125
LBB0_83:
Lloh43:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh44:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh45:
	ldr	x8, [x8]
	blr	x8
	mov	x21, x0
LBB0_84:
Lloh46:
	adrp	x23, _kLog2Table@GOTPAGE
Lloh47:
	ldr	x23, [x23, _kLog2Table@GOTPAGEOFF]
Lloh48:
	adrp	x25, _VP8LFastLog2Slow@GOTPAGE
Lloh49:
	ldr	x25, [x25, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB0_86
LBB0_85:                                ;   in Loop: Header=BB0_86 Depth=1
	ldr	x8, [x25]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	sub	w8, w21, w0
	str	w8, [x22], #4
	subs	x19, x19, #1
	b.eq	LBB0_18
LBB0_86:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x20], #4
	cmp	w0, #255
	b.hi	LBB0_85
; %bb.87:                               ;   in Loop: Header=BB0_86 Depth=1
	ldr	w0, [x23, x0, lsl #2]
	sub	w8, w21, w0
	str	w8, [x22], #4
	subs	x19, x19, #1
	b.ne	LBB0_86
	b	LBB0_18
LBB0_88:
	and	x9, x9, #0xfffffffffffffff8
	add	x11, x26, #48
	mov	w0, #1                          ; =0x1
	mov	w10, #1                         ; =0x1
	b	LBB0_90
LBB0_89:                                ;   in Loop: Header=BB0_90 Depth=1
	add	x10, x10, #8
	add	x11, x11, #64
	subs	x9, x9, #8
	b.eq	LBB0_74
LBB0_90:                                ; =>This Inner Loop Header: Depth=1
	ldur	x13, [x11, #-8]
	cmp	x13, x12
	b.ne	LBB0_98
; %bb.91:                               ;   in Loop: Header=BB0_90 Depth=1
	ldr	x12, [x11]
	cmp	x12, x13
	b.ne	LBB0_99
LBB0_92:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x13, [x11, #8]
	cmp	x13, x12
	b.ne	LBB0_100
LBB0_93:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x12, [x11, #16]
	cmp	x12, x13
	b.ne	LBB0_101
LBB0_94:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x13, [x11, #24]
	cmp	x13, x12
	b.ne	LBB0_102
LBB0_95:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x12, [x11, #32]
	cmp	x12, x13
	b.ne	LBB0_103
LBB0_96:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x13, [x11, #40]
	cmp	x13, x12
	b.ne	LBB0_104
LBB0_97:                                ;   in Loop: Header=BB0_90 Depth=1
	ldr	x12, [x11, #48]
	cmp	x12, x13
	b.eq	LBB0_89
	b	LBB0_105
LBB0_98:                                ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x12, [x11]
	cmp	x12, x13
	b.eq	LBB0_92
LBB0_99:                                ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x13, [x11, #8]
	cmp	x13, x12
	b.eq	LBB0_93
LBB0_100:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x12, [x11, #16]
	cmp	x12, x13
	b.eq	LBB0_94
LBB0_101:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x13, [x11, #24]
	cmp	x13, x12
	b.eq	LBB0_95
LBB0_102:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x12, [x11, #32]
	cmp	x12, x13
	b.eq	LBB0_96
LBB0_103:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x13, [x11, #40]
	cmp	x13, x12
	b.eq	LBB0_97
LBB0_104:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	ldr	x12, [x11, #48]
	cmp	x12, x13
	b.eq	LBB0_89
LBB0_105:                               ;   in Loop: Header=BB0_90 Depth=1
	add	x0, x0, #1
	str	x0, [x26, #24]
	b	LBB0_89
LBB0_106:
	mov	x10, #0                         ; =0x0
	and	x11, x11, #0xfffffffffffffff8
	add	x12, x26, #48
	b	LBB0_108
LBB0_107:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w14, w10, #9
	str	w14, [x0, #12]
	add	x10, x10, #8
	add	x12, x12, #64
	cmp	x11, x10
	b.eq	LBB0_124
LBB0_108:                               ; =>This Inner Loop Header: Depth=1
	ldur	x14, [x12, #-8]
	cmp	x14, x13
	b.ne	LBB0_116
; %bb.109:                              ;   in Loop: Header=BB0_108 Depth=1
	add	w13, w10, #2
	str	w13, [x0, #12]
	ldr	x13, [x12]
	cmp	x13, x14
	b.ne	LBB0_117
LBB0_110:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w14, w10, #3
	str	w14, [x0, #12]
	ldr	x14, [x12, #8]
	cmp	x14, x13
	b.ne	LBB0_118
LBB0_111:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w13, w10, #4
	str	w13, [x0, #12]
	ldr	x13, [x12, #16]
	cmp	x13, x14
	b.ne	LBB0_119
LBB0_112:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w14, w10, #5
	str	w14, [x0, #12]
	ldr	x14, [x12, #24]
	cmp	x14, x13
	b.ne	LBB0_120
LBB0_113:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w13, w10, #6
	str	w13, [x0, #12]
	ldr	x13, [x12, #32]
	cmp	x13, x14
	b.ne	LBB0_121
LBB0_114:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w14, w10, #7
	str	w14, [x0, #12]
	ldr	x14, [x12, #40]
	cmp	x14, x13
	b.ne	LBB0_122
LBB0_115:                               ;   in Loop: Header=BB0_108 Depth=1
	add	w13, w10, #8
	str	w13, [x0, #12]
	ldr	x13, [x12, #48]
	cmp	x13, x14
	b.eq	LBB0_107
	b	LBB0_123
LBB0_116:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x14, [x0, #16]!
	add	w15, w10, #1
	add	w13, w10, #2
	stp	w15, w13, [x0, #8]
	ldr	x13, [x12]
	cmp	x13, x14
	b.eq	LBB0_110
LBB0_117:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x13, [x0, #16]!
	add	w15, w10, #2
	add	w14, w10, #3
	stp	w15, w14, [x0, #8]
	ldr	x14, [x12, #8]
	cmp	x14, x13
	b.eq	LBB0_111
LBB0_118:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x14, [x0, #16]!
	add	w15, w10, #3
	add	w13, w10, #4
	stp	w15, w13, [x0, #8]
	ldr	x13, [x12, #16]
	cmp	x13, x14
	b.eq	LBB0_112
LBB0_119:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x13, [x0, #16]!
	add	w15, w10, #4
	add	w14, w10, #5
	stp	w15, w14, [x0, #8]
	ldr	x14, [x12, #24]
	cmp	x14, x13
	b.eq	LBB0_113
LBB0_120:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x14, [x0, #16]!
	add	w15, w10, #5
	add	w13, w10, #6
	stp	w15, w13, [x0, #8]
	ldr	x13, [x12, #32]
	cmp	x13, x14
	b.eq	LBB0_114
LBB0_121:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x13, [x0, #16]!
	add	w15, w10, #6
	add	w14, w10, #7
	stp	w15, w14, [x0, #8]
	ldr	x14, [x12, #40]
	cmp	x14, x13
	b.eq	LBB0_115
LBB0_122:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x14, [x0, #16]!
	add	w15, w10, #7
	add	w13, w10, #8
	stp	w15, w13, [x0, #8]
	ldr	x13, [x12, #48]
	cmp	x13, x14
	b.eq	LBB0_107
LBB0_123:                               ;   in Loop: Header=BB0_108 Depth=1
	str	x13, [x0, #16]!
	add	w14, w10, #8
	str	w14, [x0, #8]
	b	LBB0_107
LBB0_124:
	add	x10, x10, #1
LBB0_125:
	cbnz	x9, LBB0_134
LBB0_126:
	mov	x0, x25
	mov	w1, #8                          ; =0x8
	bl	_WebPSafeMalloc
	str	x0, [x28, #24]
	cbz	x0, LBB0_136
; %bb.127:
	mov	x21, x0
	cmp	w25, #1
	b.lt	LBB0_129
; %bb.128:
	lsl	x2, x25, #3
Lloh50:
	adrp	x1, l_.memset_pattern@PAGE
Lloh51:
	add	x1, x1, l_.memset_pattern@PAGEOFF
	mov	x0, x21
	bl	_memset_pattern16
LBB0_129:
	ldp	x4, x8, [sp, #40]               ; 16-byte Folded Reload
	strh	wzr, [x8]
	ldr	x8, [sp, #112]                  ; 8-byte Folded Reload
	ldr	w8, [x8]
	ldr	w9, [sp, #76]                   ; 4-byte Folded Reload
	cmp	w9, #1
	ldp	x3, x2, [sp, #80]               ; 16-byte Folded Reload
	b.lt	LBB0_172
; %bb.130:
	ldur	w10, [x29, #-88]
	ldur	x9, [x29, #-96]
	mov	w11, #42941                     ; =0xa7bd
	movk	w11, #7733, lsl #16
	mul	w11, w8, w11
	lsr	w11, w11, w10
	sxtw	x10, w11
	tbnz	w11, #31, LBB0_171
; %bb.131:
	ldr	w11, [x9, w11, sxtw #2]
	cmp	w11, w8
	b.ne	LBB0_171
; %bb.132:
	ldr	x8, [x22, #3232]
	add	w9, w10, #280
	ldr	w8, [x8, w9, sxtw #2]
	add	x8, x8, x8, lsl #4
	lsl	x8, x8, #2
	b	LBB0_173
LBB0_133:                               ;   in Loop: Header=BB0_134 Depth=1
	add	x10, x10, #1
	str	w10, [x0, #12]
	subs	x9, x9, #1
	b.eq	LBB0_126
LBB0_134:                               ; =>This Inner Loop Header: Depth=1
	mov	x11, x13
	ldr	x13, [x8, x10, lsl #3]
	cmp	x13, x11
	b.eq	LBB0_133
; %bb.135:                              ;   in Loop: Header=BB0_134 Depth=1
	str	x13, [x0, #16]!
	str	w10, [x0, #8]
	b	LBB0_133
LBB0_136:
	mov	x0, x26
	bl	_CostManagerClear
	mov	w19, #0                         ; =0x0
	ldr	x28, [sp, #48]                  ; 8-byte Folded Reload
	ldr	w21, [sp, #76]                  ; 4-byte Folded Reload
	cmp	w21, #1
	b.lt	LBB0_138
LBB0_137:
	sub	x0, x29, #96
	bl	_VP8LColorCacheClear
LBB0_138:
	mov	x0, x26
	bl	_CostManagerClear
	mov	x0, x22
	bl	_WebPSafeFree
	mov	x0, x26
	bl	_WebPSafeFree
	cbz	w19, LBB0_160
; %bb.139:
	add	x8, x28, x25, lsl #1
	sub	x9, x8, #2
	mov	x19, x8
	cmp	x9, x28
	b.lo	LBB0_141
LBB0_140:                               ; =>This Inner Loop Header: Depth=1
	ldrh	w10, [x9]
	strh	w10, [x19, #-2]!
	sub	x9, x9, x10, lsl #1
	cmp	x9, x28
	b.hs	LBB0_140
LBB0_141:
	sub	x23, x8, x19
	lsr	x20, x23, #1
	cmp	w21, #1
	b.lt	LBB0_162
; %bb.142:
	sub	x0, x29, #96
	mov	x1, x21
	bl	_VP8LColorCacheInit
	cbz	w0, LBB0_160
; %bb.143:
	mov	x0, x27
	bl	_VP8LClearBackwardRefs
	cmp	w20, #0
	b.le	LBB0_168
; %bb.144:
	str	w21, [sp, #76]                  ; 4-byte Folded Spill
	mov	x20, #0                         ; =0x0
	mov	w21, #0                         ; =0x0
	mov	w22, #42941                     ; =0xa7bd
	movk	w22, #7733, lsl #16
	ubfx	x23, x23, #1, #31
	mov	w25, #6                         ; =0x6
	b	LBB0_148
LBB0_145:                               ;   in Loop: Header=BB0_148 Depth=1
	str	w9, [x10, w8, sxtw #2]
	ldr	x8, [sp, #112]                  ; 8-byte Folded Reload
	ldr	w8, [x8, x24, lsl #2]
	mov	w9, #65536                      ; =0x10000
LBB0_146:                               ;   in Loop: Header=BB0_148 Depth=1
                                        ; kill: def $w8 killed $w8 killed $x8 def $x8
	orr	x1, x9, x8, lsl #32
	mov	x0, x27
	bl	_VP8LBackwardRefsCursorAdd
LBB0_147:                               ;   in Loop: Header=BB0_148 Depth=1
	add	w21, w21, w26
	add	x20, x20, #1
	cmp	x20, x23
	b.eq	LBB0_167
LBB0_148:                               ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB0_155 Depth 2
                                        ;     Child Loop BB0_159 Depth 2
	ldrh	w8, [x19, x20, lsl #1]
	and	w26, w8, #0xffff
	mov	w24, w21
	cmp	w26, #1
	b.ne	LBB0_152
; %bb.149:                              ;   in Loop: Header=BB0_148 Depth=1
	ldr	x8, [sp, #112]                  ; 8-byte Folded Reload
	ldr	w9, [x8, w21, uxtw #2]
	ldur	x10, [x29, #-96]
	ldur	w8, [x29, #-88]
	mul	w11, w9, w22
	lsr	w8, w11, w8
	ldr	w11, [x10, w8, sxtw #2]
	cmp	w11, w9
	b.ne	LBB0_145
; %bb.150:                              ;   in Loop: Header=BB0_148 Depth=1
	tbnz	w8, #31, LBB0_145
; %bb.151:                              ;   in Loop: Header=BB0_148 Depth=1
	mov	w9, #65537                      ; =0x10001
	b	LBB0_146
LBB0_152:                               ;   in Loop: Header=BB0_148 Depth=1
	ldr	x8, [sp, #104]                  ; 8-byte Folded Reload
	ldr	x8, [x8]
	ldr	w8, [x8, w21, uxtw #2]
	lsl	x8, x8, #20
	and	x8, x8, #0xfffff00000000
	orr	x8, x8, x26, lsl #16
	orr	x1, x8, #0x2
	mov	x0, x27
	bl	_VP8LBackwardRefsCursorAdd
	cbz	w26, LBB0_147
; %bb.153:                              ;   in Loop: Header=BB0_148 Depth=1
	mov	x11, #0                         ; =0x0
	ldur	x8, [x29, #-96]
	sub	x9, x26, #1
	mov	x10, #-6148914691236517206      ; =0xaaaaaaaaaaaaaaaa
	movk	x10, #43691
	umulh	x10, x9, x10
	lsr	x10, x10, #2
	msub	x9, x10, x25, x9
	add	x10, x9, #1
	cmp	x10, #6
	csinc	x9, xzr, x9, eq
	cmp	w26, #6
	b.lo	LBB0_157
; %bb.154:                              ;   in Loop: Header=BB0_148 Depth=1
	mov	x11, #0                         ; =0x0
	ldr	x12, [sp, #112]                 ; 8-byte Folded Reload
	add	x12, x12, x24, lsl #2
	add	x12, x12, #12
	sub	x13, x9, x26
LBB0_155:                               ;   Parent Loop BB0_148 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldur	w14, [x12, #-12]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldur	w14, [x12, #-8]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldur	w14, [x12, #-4]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12, #4]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12, #8]
	ldur	w15, [x29, #-88]
	mul	w16, w14, w22
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	sub	x11, x11, #6
	add	x12, x12, #24
	cmp	x13, x11
	b.ne	LBB0_155
; %bb.156:                              ;   in Loop: Header=BB0_148 Depth=1
	neg	x11, x11
LBB0_157:                               ;   in Loop: Header=BB0_148 Depth=1
	cmp	x10, #6
	b.eq	LBB0_147
; %bb.158:                              ;   in Loop: Header=BB0_148 Depth=1
	lsl	x10, x11, #2
	add	x10, x10, x24, lsl #2
	ldr	x11, [sp, #112]                 ; 8-byte Folded Reload
	add	x10, x11, x10
LBB0_159:                               ;   Parent Loop BB0_148 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	w11, [x10], #4
	ldur	w12, [x29, #-88]
	mul	w13, w11, w22
	lsr	w12, w13, w12
	str	w11, [x8, w12, sxtw #2]
	subs	x9, x9, #1
	b.ne	LBB0_159
	b	LBB0_147
LBB0_160:
	mov	w20, #0                         ; =0x0
LBB0_161:
	mov	x0, x28
	bl	_WebPSafeFree
	mov	x0, x20
	ldp	x29, x30, [sp, #224]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #208]            ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #192]            ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #176]            ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #160]            ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #144]            ; 16-byte Folded Reload
	add	sp, sp, #240
	ret
LBB0_162:
	mov	x0, x27
	bl	_VP8LClearBackwardRefs
	cmp	w20, #0
	b.le	LBB0_170
; %bb.163:
	str	w21, [sp, #76]                  ; 4-byte Folded Spill
	mov	w20, #0                         ; =0x0
	ubfx	x21, x23, #1, #31
	mov	w22, #65536                     ; =0x10000
	b	LBB0_165
LBB0_164:                               ;   in Loop: Header=BB0_165 Depth=1
	ldr	x8, [sp, #112]                  ; 8-byte Folded Reload
	ldr	w8, [x8, w20, uxtw #2]
	orr	x1, x22, x8, lsl #32
	mov	x0, x27
	bl	_VP8LBackwardRefsCursorAdd
	add	w20, w20, w23
	subs	x21, x21, #1
	b.eq	LBB0_167
LBB0_165:                               ; =>This Inner Loop Header: Depth=1
	ldrh	w23, [x19], #2
	cmp	w23, #1
	b.eq	LBB0_164
; %bb.166:                              ;   in Loop: Header=BB0_165 Depth=1
	ldr	x8, [sp, #104]                  ; 8-byte Folded Reload
	ldr	x8, [x8]
	ldr	w8, [x8, w20, uxtw #2]
	lsl	x8, x8, #20
	and	x8, x8, #0xfffff00000000
	orr	x8, x8, x23, lsl #16
	orr	x1, x8, #0x2
	mov	x0, x27
	bl	_VP8LBackwardRefsCursorAdd
	add	w20, w20, w23
	subs	x21, x21, #1
	b.ne	LBB0_165
LBB0_167:
	ldr	w8, [x27, #4]
	cmp	w8, #0
	cset	w20, eq
	ldr	w8, [sp, #76]                   ; 4-byte Folded Reload
	cmp	w8, #1
	b.ge	LBB0_169
	b	LBB0_161
LBB0_168:
	ldr	w8, [x27, #4]
	cmp	w8, #0
	cset	w20, eq
LBB0_169:
	sub	x0, x29, #96
	bl	_VP8LColorCacheClear
	b	LBB0_161
LBB0_170:
	ldr	w8, [x27, #4]
	cmp	w8, #0
	cset	w20, eq
	b	LBB0_161
LBB0_171:
	str	w8, [x9, x10, lsl #2]
LBB0_172:
	lsr	x9, x8, #22
	and	x9, x9, #0x3fc
	ldr	w9, [x22, x9]
	ubfx	x10, x8, #16, #8
	ldr	w10, [x2, x10, lsl #2]
	ldr	x11, [x22, #3232]
	ubfx	x12, x8, #8, #8
	ldr	w11, [x11, x12, lsl #2]
	add	x10, x10, x11
	add	x9, x10, x9
	and	x8, x8, #0xff
	ldr	w8, [x3, x8, lsl #2]
	add	x8, x9, x8
	mov	w9, #82                         ; =0x52
	mul	x8, x8, x9
LBB0_173:
	str	x27, [sp]                       ; 8-byte Folded Spill
	add	x8, x8, #50
	mov	x5, #36701                      ; =0x8f5d
	movk	x5, #62914, lsl #16
	movk	x5, #23592, lsl #32
	movk	x5, #655, lsl #48
	umulh	x8, x8, x5
	ldr	x9, [x21]
	cmp	x9, x8
	b.le	LBB0_175
; %bb.174:
	str	x8, [x21]
	mov	w8, #1                          ; =0x1
	ldr	x9, [sp, #48]                   ; 8-byte Folded Reload
	strh	w8, [x9]
LBB0_175:
	cmp	w25, #2
	b.lt	LBB0_222
; %bb.176:
	mov	w6, #0                          ; =0x0
	mov	x8, #-1                         ; =0xffffffffffffffff
	str	x8, [sp, #24]                   ; 8-byte Folded Spill
	mov	w9, #-1                         ; =0xffffffff
	mov	w21, #8                         ; =0x8
	mov	w25, #33208                     ; =0x81b8
	mov	w19, #33216                     ; =0x81c0
	mov	w24, #1                         ; =0x1
	mov	w27, #-1                        ; =0xffffffff
	mov	w22, #-1                        ; =0xffffffff
	str	x20, [sp, #8]                   ; 8-byte Folded Spill
	b	LBB0_178
LBB0_177:                               ;   in Loop: Header=BB0_178 Depth=1
	add	x24, x24, #1
	add	x21, x21, #4
	ldr	x8, [sp, #56]                   ; 8-byte Folded Reload
	cmp	x24, x8
	b.eq	LBB0_222
LBB0_178:                               ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB0_197 Depth 2
                                        ;     Child Loop BB0_204 Depth 2
                                        ;     Child Loop BB0_209 Depth 2
                                        ;     Child Loop BB0_216 Depth 2
	mov	x10, x22
	mov	x12, x27
	ldr	x8, [x28, #24]
	sub	x13, x24, #1
	ldr	x23, [x8, x13, lsl #3]
	ldp	x11, x15, [sp, #104]            ; 16-byte Folded Reload
	ldr	x11, [x11]
	ldr	w14, [x11, x24, lsl #2]
	ldr	w15, [x15, x24, lsl #2]
	ldr	w16, [sp, #76]                  ; 4-byte Folded Reload
	cmp	w16, #1
	ldr	x1, [sp, #96]                   ; 8-byte Folded Reload
	b.lt	LBB0_183
; %bb.179:                              ;   in Loop: Header=BB0_178 Depth=1
	ldur	w17, [x29, #-88]
	ldur	x16, [x29, #-96]
	mov	w0, #42941                      ; =0xa7bd
	movk	w0, #7733, lsl #16
	mul	w0, w15, w0
	lsr	w0, w0, w17
	sxtw	x17, w0
	tbnz	w0, #31, LBB0_182
; %bb.180:                              ;   in Loop: Header=BB0_178 Depth=1
	ldr	w0, [x16, w0, sxtw #2]
	cmp	w0, w15
	b.ne	LBB0_182
; %bb.181:                              ;   in Loop: Header=BB0_178 Depth=1
	ldr	x15, [x1, #3232]
	add	w16, w17, #280
	ldr	w15, [x15, w16, sxtw #2]
	add	x15, x15, x15, lsl #4
	lsl	x15, x15, #2
	add	x15, x15, #50
	umulh	x15, x15, x5
	ldr	x16, [x8, x24, lsl #3]
	add	x15, x15, x23
	cmp	x16, x15
	b.gt	LBB0_184
	b	LBB0_185
LBB0_182:                               ;   in Loop: Header=BB0_178 Depth=1
	str	w15, [x16, x17, lsl #2]
LBB0_183:                               ;   in Loop: Header=BB0_178 Depth=1
	lsr	x16, x15, #22
	and	x16, x16, #0x3fc
	ldr	w16, [x1, x16]
	ubfx	x17, x15, #16, #8
	ldr	w17, [x2, x17, lsl #2]
	ldr	x0, [x1, #3232]
	ubfx	x1, x15, #8, #8
	ldr	w0, [x0, x1, lsl #2]
	add	x17, x17, x0
	add	x16, x17, x16
	and	x15, x15, #0xff
	ldr	w15, [x3, x15, lsl #2]
	add	x15, x16, x15
	mov	w16, #82                        ; =0x52
	mul	x15, x15, x16
	add	x15, x15, #50
	umulh	x15, x15, x5
	ldr	x16, [x8, x24, lsl #3]
	add	x15, x15, x23
	cmp	x16, x15
	b.le	LBB0_185
LBB0_184:                               ;   in Loop: Header=BB0_178 Depth=1
	str	x15, [x8, x24, lsl #3]
	ldr	x15, [sp, #48]                  ; 8-byte Folded Reload
	mov	w16, #1                         ; =0x1
	strh	w16, [x15, x24, lsl #1]
LBB0_185:                               ;   in Loop: Header=BB0_178 Depth=1
	lsr	w22, w14, #12
	and	w27, w14, #0xfff
	cmp	w27, #2
	b.lo	LBB0_190
; %bb.186:                              ;   in Loop: Header=BB0_178 Depth=1
	cmp	w22, w10
	b.ne	LBB0_191
; %bb.187:                              ;   in Loop: Header=BB0_178 Depth=1
	add	w12, w13, w12
	sub	w12, w12, #1
	cmp	w9, #0
	csel	w6, w6, w12, eq
	add	w9, w24, w27
	sub	w9, w9, #1
	cmp	w9, w6
	b.le	LBB0_193
; %bb.188:                              ;   in Loop: Header=BB0_178 Depth=1
	sxtw	x9, w6
	cmp	x24, x9
	b.le	LBB0_196
; %bb.189:                              ;   in Loop: Header=BB0_178 Depth=1
	mov	w20, #0                         ; =0x0
	mov	x2, x24
	b	LBB0_201
LBB0_190:                               ;   in Loop: Header=BB0_178 Depth=1
	ldr	x8, [x26]
	cbnz	x8, LBB0_216
	b	LBB0_177
LBB0_191:                               ;   in Loop: Header=BB0_178 Depth=1
	mov	x25, x20
	mov	x20, x6
	ldr	w0, [sp, #36]                   ; 4-byte Folded Reload
	mov	x1, x22
	bl	_VP8LDistanceToPlaneCode
	cmp	w0, #511
	b.gt	LBB0_194
; %bb.192:                              ;   in Loop: Header=BB0_178 Depth=1
Lloh52:
	adrp	x8, _kPrefixEncodeCode@GOTPAGE
Lloh53:
	ldr	x8, [x8, _kPrefixEncodeCode@GOTPAGEOFF]
	add	x8, x8, w0, sxtw #1
	ldrsb	w9, [x8]
	ldrsb	w8, [x8, #1]
	b	LBB0_195
LBB0_193:                               ;   in Loop: Header=BB0_178 Depth=1
	mov	w9, #0                          ; =0x0
	ldr	x8, [x26]
	cbnz	x8, LBB0_216
	b	LBB0_177
LBB0_194:                               ;   in Loop: Header=BB0_178 Depth=1
	sub	w9, w0, #1
	clz	w8, w9
	eor	w10, w8, #0x1f
	sub	w8, w10, #1
	lsr	w9, w9, w8
	and	w9, w9, #0x1
	orr	w9, w9, w10, lsl #1
LBB0_195:                               ;   in Loop: Header=BB0_178 Depth=1
	ldr	x10, [sp, #64]                  ; 8-byte Folded Reload
	ldr	w9, [x10, w9, sxtw #2]
	sxtw	x8, w8
	add	x8, x9, x8, lsl #23
	str	x8, [sp, #24]                   ; 8-byte Folded Spill
	add	x1, x8, x23
	mov	x0, x26
	mov	x2, x24
	mov	x3, x27
	bl	_PushInterval
	mov	w9, #1                          ; =0x1
	ldp	x3, x2, [sp, #80]               ; 16-byte Folded Reload
	ldr	x4, [sp, #40]                   ; 8-byte Folded Reload
	mov	x5, #36701                      ; =0x8f5d
	movk	x5, #62914, lsl #16
	movk	x5, #23592, lsl #32
	movk	x5, #655, lsl #48
	mov	x6, x20
	mov	x20, x25
	mov	w25, #33208                     ; =0x81b8
	ldr	x8, [x26]
	cbnz	x8, LBB0_216
	b	LBB0_177
LBB0_196:                               ;   in Loop: Header=BB0_178 Depth=1
	add	w2, w6, #1
	add	x13, x11, x21
	mov	x12, x24
LBB0_197:                               ;   Parent Loop BB0_178 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	w14, [x13], #4
	cmp	w10, w14, lsr #12
	b.ne	LBB0_200
; %bb.198:                              ;   in Loop: Header=BB0_197 Depth=2
	add	x12, x12, #1
	sub	x15, x12, #1
	cmp	x15, x9
	b.lt	LBB0_197
; %bb.199:                              ;   in Loop: Header=BB0_178 Depth=1
	and	w20, w14, #0xfff
	b	LBB0_201
LBB0_200:                               ;   in Loop: Header=BB0_178 Depth=1
	ldr	w9, [x11, w12, uxtw #2]
	and	w20, w9, #0xfff
	mov	x2, x12
LBB0_201:                               ;   in Loop: Header=BB0_178 Depth=1
	sub	w10, w2, #1
	ldr	x9, [x26]
	sxtw	x23, w10
	cbz	x9, LBB0_213
; %bb.202:                              ;   in Loop: Header=BB0_178 Depth=1
	mov	x10, x9
	b	LBB0_204
LBB0_203:                               ;   in Loop: Header=BB0_204 Depth=2
	cbz	x10, LBB0_209
LBB0_204:                               ;   Parent Loop BB0_178 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x11, x10
	ldr	w10, [x10, #8]
	cmp	w10, w2
	b.ge	LBB0_209
; %bb.205:                              ;   in Loop: Header=BB0_204 Depth=2
	ldr	x10, [x11, #32]
	ldr	w12, [x11, #12]
	cmp	w12, w2
	b.lt	LBB0_203
; %bb.206:                              ;   in Loop: Header=BB0_204 Depth=2
	ldr	x12, [x11]
	ldr	x13, [x8, x23, lsl #3]
	cmp	x13, x12
	b.le	LBB0_203
; %bb.207:                              ;   in Loop: Header=BB0_204 Depth=2
	ldr	w11, [x11, #16]
	sub	w11, w23, w11
	str	x12, [x8, x23, lsl #3]
	add	w11, w11, #1
	ldr	x12, [x28, #32]
	strh	w11, [x12, x23, lsl #1]
	b	LBB0_203
LBB0_208:                               ;   in Loop: Header=BB0_209 Depth=2
	cbz	x9, LBB0_213
LBB0_209:                               ;   Parent Loop BB0_178 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x10, x9
	ldr	w9, [x9, #8]
	cmp	w9, w2
	b.gt	LBB0_213
; %bb.210:                              ;   in Loop: Header=BB0_209 Depth=2
	ldr	x9, [x10, #32]
	ldr	w11, [x10, #12]
	cmp	w11, w2
	b.le	LBB0_208
; %bb.211:                              ;   in Loop: Header=BB0_209 Depth=2
	ldr	x11, [x10]
	ldr	x12, [x8, w2, uxtw #3]
	cmp	x12, x11
	b.le	LBB0_208
; %bb.212:                              ;   in Loop: Header=BB0_209 Depth=2
	ldr	w10, [x10, #16]
	sub	w10, w2, w10
	str	x11, [x8, w2, uxtw #3]
	add	w10, w10, #1
	ldr	x11, [x28, #32]
	strh	w10, [x11, w2, uxtw #1]
	b	LBB0_208
LBB0_213:                               ;   in Loop: Header=BB0_178 Depth=1
	ldr	x8, [x8, x23, lsl #3]
	ldr	x9, [sp, #24]                   ; 8-byte Folded Reload
	add	x1, x8, x9
	mov	x0, x26
	mov	x3, x20
	bl	_PushInterval
	mov	w9, #0                          ; =0x0
	add	w6, w23, w20
	ldp	x3, x2, [sp, #80]               ; 16-byte Folded Reload
	ldr	x4, [sp, #40]                   ; 8-byte Folded Reload
	mov	x5, #36701                      ; =0x8f5d
	movk	x5, #62914, lsl #16
	movk	x5, #23592, lsl #32
	movk	x5, #655, lsl #48
	ldr	x20, [sp, #8]                   ; 8-byte Folded Reload
	ldr	x8, [x26]
	cbnz	x8, LBB0_216
	b	LBB0_177
LBB0_214:                               ;   in Loop: Header=BB0_216 Depth=2
	cmp	x20, x10
	ccmp	x4, x10, #2, hs
	csel	x11, x19, x25, hi
	ldr	x12, [x26, x11]
	str	x10, [x26, x11]
	str	x12, [x10, #32]
	ldr	w10, [x26, #8]
	sub	w10, w10, #1
	str	w10, [x26, #8]
LBB0_215:                               ;   in Loop: Header=BB0_216 Depth=2
	cbz	x8, LBB0_177
LBB0_216:                               ;   Parent Loop BB0_178 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x10, x8
	ldrsw	x8, [x8, #8]
	cmp	x24, x8
	b.lt	LBB0_177
; %bb.217:                              ;   in Loop: Header=BB0_216 Depth=2
	ldr	x8, [x10, #32]
	ldrsw	x11, [x10, #12]
	cmp	x24, x11
	b.ge	LBB0_220
; %bb.218:                              ;   in Loop: Header=BB0_216 Depth=2
	ldr	x11, [x10]
	ldr	x12, [x28, #24]
	ldr	x13, [x12, x24, lsl #3]
	cmp	x13, x11
	b.le	LBB0_215
; %bb.219:                              ;   in Loop: Header=BB0_216 Depth=2
	ldr	w10, [x10, #16]
	sub	w10, w24, w10
	str	x11, [x12, x24, lsl #3]
	add	w10, w10, #1
	ldr	x11, [x28, #32]
	strh	w10, [x11, x24, lsl #1]
	b	LBB0_215
LBB0_220:                               ;   in Loop: Header=BB0_216 Depth=2
	ldr	x11, [x10, #24]
	add	x12, x11, #32
	cmp	x11, #0
	csel	x12, x26, x12, eq
	str	x8, [x12]
	cbz	x8, LBB0_214
; %bb.221:                              ;   in Loop: Header=BB0_216 Depth=2
	str	x11, [x8, #24]
	b	LBB0_214
LBB0_222:
	ldr	x8, [sp, #16]                   ; 8-byte Folded Reload
	ldr	w8, [x8, #4]
	cmp	w8, #0
	cset	w19, eq
	ldp	x28, x25, [sp, #48]             ; 16-byte Folded Reload
	ldr	x27, [sp]                       ; 8-byte Folded Reload
	ldr	w21, [sp, #76]                  ; 4-byte Folded Reload
	ldr	x22, [sp, #96]                  ; 8-byte Folded Reload
	cmp	w21, #1
	b.ge	LBB0_137
	b	LBB0_138
	.loh AdrpLdrGot	Lloh0, Lloh1
	.loh AdrpLdrGot	Lloh4, Lloh5
	.loh AdrpLdrGot	Lloh2, Lloh3
	.loh AdrpLdrGot	Lloh6, Lloh7
	.loh AdrpLdrGot	Lloh8, Lloh9
	.loh AdrpLdrGotLdr	Lloh10, Lloh11, Lloh12
	.loh AdrpLdrGot	Lloh15, Lloh16
	.loh AdrpLdrGot	Lloh13, Lloh14
	.loh AdrpLdrGot	Lloh17, Lloh18
	.loh AdrpLdrGotLdr	Lloh19, Lloh20, Lloh21
	.loh AdrpLdrGot	Lloh24, Lloh25
	.loh AdrpLdrGot	Lloh22, Lloh23
	.loh AdrpLdr	Lloh28, Lloh29
	.loh AdrpLdr	Lloh26, Lloh27
	.loh AdrpLdrGot	Lloh30, Lloh31
	.loh AdrpLdrGotLdr	Lloh32, Lloh33, Lloh34
	.loh AdrpLdrGot	Lloh37, Lloh38
	.loh AdrpLdrGot	Lloh35, Lloh36
	.loh AdrpLdrGot	Lloh39, Lloh40
	.loh AdrpLdr	Lloh41, Lloh42
	.loh AdrpLdrGotLdr	Lloh43, Lloh44, Lloh45
	.loh AdrpLdrGot	Lloh48, Lloh49
	.loh AdrpLdrGot	Lloh46, Lloh47
	.loh AdrpAdd	Lloh50, Lloh51
	.loh AdrpLdrGot	Lloh52, Lloh53
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function PushInterval
_PushInterval:                          ; @PushInterval
	.cfi_startproc
; %bb.0:
	sub	sp, sp, #128
	stp	x28, x27, [sp, #32]             ; 16-byte Folded Spill
	stp	x26, x25, [sp, #48]             ; 16-byte Folded Spill
	stp	x24, x23, [sp, #64]             ; 16-byte Folded Spill
	stp	x22, x21, [sp, #80]             ; 16-byte Folded Spill
	stp	x20, x19, [sp, #96]             ; 16-byte Folded Spill
	stp	x29, x30, [sp, #112]            ; 16-byte Folded Spill
	add	x29, sp, #112
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	mov	x21, x3
	mov	x20, x2
	mov	x19, x1
	mov	x22, x0
	cmp	w3, #9
	b.gt	LBB1_6
; %bb.1:
	cmp	w21, #1
	b.lt	LBB1_28
; %bb.2:
	mov	x8, #0                          ; =0x0
	add	x9, x22, #8, lsl #12            ; =32768
	add	w13, w21, w20
	add	x10, x22, #32
	ldr	x11, [x9, #24]
	sxtw	x12, w20
	sxtw	x13, w13
	b	LBB1_4
LBB1_3:                                 ;   in Loop: Header=BB1_4 Depth=1
	add	x12, x12, #1
	add	x8, x8, #1
	cmp	x12, x13
	b.ge	LBB1_28
LBB1_4:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x14, [x10, x8, lsl #3]
	ldr	x15, [x11, x12, lsl #3]
	add	x14, x14, x19
	cmp	x15, x14
	b.le	LBB1_3
; %bb.5:                                ;   in Loop: Header=BB1_4 Depth=1
	str	x14, [x11, x12, lsl #3]
	add	w14, w8, #1
	ldr	x15, [x9, #32]
	strh	w14, [x15, x12, lsl #1]
	b	LBB1_3
LBB1_6:
	ldr	x8, [x22, #24]
	cbz	x8, LBB1_28
; %bb.7:
	mov	x27, #0                         ; =0x0
	ldr	x9, [x22, #16]
	ldr	x28, [x22]
	mov	w8, #32808                      ; =0x8028
	add	x8, x22, x8
	stp	x8, x9, [sp, #16]               ; 16-byte Folded Spill
	mov	w8, #33168                      ; =0x8190
	add	x8, x22, x8
	str	x8, [sp, #8]                    ; 8-byte Folded Spill
	b	LBB1_10
LBB1_8:                                 ;   in Loop: Header=BB1_10 Depth=1
	mov	x25, #0                         ; =0x0
LBB1_9:                                 ;   in Loop: Header=BB1_10 Depth=1
	mov	x0, x22
	mov	x1, x25
	mov	x2, x24
	mov	x3, x20
	mov	x4, x26
	mov	x5, x23
	bl	_InsertInterval
	add	x27, x27, #1
	ldr	x8, [x22, #24]
	mov	x28, x25
	cmp	x27, x8
	b.hs	LBB1_28
LBB1_10:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_15 Depth 2
	ldr	x8, [sp, #24]                   ; 8-byte Folded Reload
	add	x8, x8, x27, lsl #4
	ldr	w9, [x8, #8]
	cmp	w9, w21
	b.ge	LBB1_28
; %bb.11:                               ;   in Loop: Header=BB1_10 Depth=1
	add	w26, w9, w20
	ldr	w9, [x8, #12]
	cmp	w9, w21
	csel	w9, w9, w21, lt
	add	w23, w9, w20
	ldr	x8, [x8]
	add	x24, x8, x19
	cbz	x28, LBB1_8
; %bb.12:                               ;   in Loop: Header=BB1_10 Depth=1
	mov	x4, x26
	b	LBB1_15
LBB1_13:                                ;   in Loop: Header=BB1_15 Depth=2
	mov	x0, x22
	mov	x1, x25
	mov	x2, x24
	mov	x3, x20
	bl	_InsertInterval
	mov	x4, x26
	cmp	w26, w23
	b.ge	LBB1_9
LBB1_14:                                ;   in Loop: Header=BB1_15 Depth=2
	cbz	x28, LBB1_24
LBB1_15:                                ;   Parent Loop BB1_10 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x25, x28
	ldr	w5, [x28, #8]
	cmp	w5, w23
	b.ge	LBB1_25
; %bb.16:                               ;   in Loop: Header=BB1_15 Depth=2
	ldr	x28, [x25, #32]
	ldr	w26, [x25, #12]
	cmp	w4, w26
	b.ge	LBB1_14
; %bb.17:                               ;   in Loop: Header=BB1_15 Depth=2
	ldr	x2, [x25]
	cmp	x24, x2
	b.ge	LBB1_13
; %bb.18:                               ;   in Loop: Header=BB1_15 Depth=2
	cmp	w4, w5
	b.le	LBB1_20
; %bb.19:                               ;   in Loop: Header=BB1_15 Depth=2
	str	w4, [x25, #12]
	cmp	w23, w26
	b.ge	LBB1_14
	b	LBB1_26
LBB1_20:                                ;   in Loop: Header=BB1_15 Depth=2
	cmp	w26, w23
	b.gt	LBB1_27
; %bb.21:                               ;   in Loop: Header=BB1_15 Depth=2
	ldr	x8, [x25, #24]
	add	x9, x8, #32
	cmp	x8, #0
	csel	x9, x22, x9, eq
	str	x28, [x9]
	cbz	x28, LBB1_23
; %bb.22:                               ;   in Loop: Header=BB1_15 Depth=2
	str	x8, [x28, #24]
LBB1_23:                                ;   in Loop: Header=BB1_15 Depth=2
	ldp	x9, x8, [sp, #8]                ; 16-byte Folded Reload
	cmp	x9, x25
	ccmp	x8, x25, #2, hs
	mov	w8, #33208                      ; =0x81b8
	mov	w9, #33216                      ; =0x81c0
	csel	x8, x9, x8, hi
	ldr	x9, [x22, x8]
	str	x25, [x22, x8]
	str	x9, [x25, #32]
	ldr	w8, [x22, #8]
	sub	w8, w8, #1
	str	w8, [x22, #8]
	b	LBB1_14
LBB1_24:                                ;   in Loop: Header=BB1_10 Depth=1
	mov	x25, #0                         ; =0x0
LBB1_25:                                ;   in Loop: Header=BB1_10 Depth=1
	mov	x26, x4
	b	LBB1_9
LBB1_26:                                ;   in Loop: Header=BB1_10 Depth=1
	ldr	w3, [x25, #16]
	mov	x0, x22
	mov	x1, x25
	mov	x28, x4
	mov	x4, x23
	mov	x5, x26
	bl	_InsertInterval
	ldr	x25, [x25, #32]
	mov	x26, x28
	b	LBB1_9
LBB1_27:                                ;   in Loop: Header=BB1_10 Depth=1
	str	w23, [x25, #8]
	mov	x26, x4
	b	LBB1_9
LBB1_28:
	ldp	x29, x30, [sp, #112]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #96]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #80]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #64]             ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #48]             ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #32]             ; 16-byte Folded Reload
	add	sp, sp, #128
	ret
	.cfi_endproc
                                        ; -- End function
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; -- Begin function CostManagerClear
lCPI2_0:
	.quad	33128                           ; 0x8168
	.quad	33168                           ; 0x8190
	.section	__TEXT,__text,regular,pure_instructions
	.p2align	2
_CostManagerClear:                      ; @CostManagerClear
	.cfi_startproc
; %bb.0:
	cbz	x0, LBB2_14
; %bb.1:
	stp	x24, x23, [sp, #-64]!           ; 16-byte Folded Spill
	stp	x22, x21, [sp, #16]             ; 16-byte Folded Spill
	stp	x20, x19, [sp, #32]             ; 16-byte Folded Spill
	stp	x29, x30, [sp, #48]             ; 16-byte Folded Spill
	add	x29, sp, #48
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	mov	x19, x0
	add	x20, x0, #8, lsl #12            ; =32768
	ldr	x0, [x20, #24]
	bl	_WebPSafeFree
	ldr	x0, [x19, #16]
	bl	_WebPSafeFree
	ldr	x0, [x19]
	cbz	x0, LBB2_7
; %bb.2:
	mov	w8, #32808                      ; =0x8028
	add	x21, x19, x8
	mov	w8, #33168                      ; =0x8190
	add	x22, x19, x8
	b	LBB2_5
LBB2_3:                                 ;   in Loop: Header=BB2_5 Depth=1
	bl	_WebPSafeFree
LBB2_4:                                 ;   in Loop: Header=BB2_5 Depth=1
	mov	x0, x23
	cbz	x23, LBB2_7
LBB2_5:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x23, [x0, #32]
	cmp	x21, x0
	b.hi	LBB2_3
; %bb.6:                                ;   in Loop: Header=BB2_5 Depth=1
	cmp	x22, x0
	b.hs	LBB2_4
	b	LBB2_3
LBB2_7:
	str	xzr, [x19]
	ldr	x0, [x20, #448]
	cbz	x0, LBB2_13
; %bb.8:
	mov	w8, #32808                      ; =0x8028
	add	x21, x19, x8
	mov	w8, #33168                      ; =0x8190
	add	x22, x19, x8
	b	LBB2_11
LBB2_9:                                 ;   in Loop: Header=BB2_11 Depth=1
	bl	_WebPSafeFree
LBB2_10:                                ;   in Loop: Header=BB2_11 Depth=1
	mov	x0, x23
	cbz	x23, LBB2_13
LBB2_11:                                ; =>This Inner Loop Header: Depth=1
	ldr	x23, [x0, #32]
	cmp	x21, x0
	b.hi	LBB2_9
; %bb.12:                               ;   in Loop: Header=BB2_11 Depth=1
	cmp	x22, x0
	b.hs	LBB2_10
	b	LBB2_9
LBB2_13:
	mov	x0, x19
	mov	w1, #33224                      ; =0x81c8
	bl	_bzero
	mov	w8, #32808                      ; =0x8028
	add	x8, x19, x8
	str	xzr, [x20, #72]
	mov	w9, #32848                      ; =0x8050
	add	x9, x19, x9
	str	x8, [x20, #112]
	mov	w8, #32888                      ; =0x8078
	add	x8, x19, x8
	str	x9, [x20, #152]
	mov	w9, #32928                      ; =0x80a0
	add	x9, x19, x9
	str	x8, [x20, #192]
	mov	w8, #32968                      ; =0x80c8
	add	x8, x19, x8
	str	x9, [x20, #232]
	mov	w9, #33008                      ; =0x80f0
	add	x9, x19, x9
	str	x8, [x20, #272]
	mov	w8, #33048                      ; =0x8118
	add	x8, x19, x8
	str	x9, [x20, #312]
	mov	w9, #33088                      ; =0x8140
	add	x9, x19, x9
	dup.2d	v0, x19
	str	x8, [x20, #352]
Lloh54:
	adrp	x8, lCPI2_0@PAGE
Lloh55:
	ldr	q1, [x8, lCPI2_0@PAGEOFF]
	add.2d	v0, v0, v1
	str	x9, [x20, #392]
	str	q0, [x19, #33200]
	ldp	x29, x30, [sp, #48]             ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #32]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #16]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp], #64             ; 16-byte Folded Reload
LBB2_14:
	ret
	.loh AdrpLdr	Lloh54, Lloh55
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function InsertInterval
_InsertInterval:                        ; @InsertInterval
	.cfi_startproc
; %bb.0:
	cmp	w4, w5
	b.ge	LBB3_24
; %bb.1:
	stp	x26, x25, [sp, #-80]!           ; 16-byte Folded Spill
	stp	x24, x23, [sp, #16]             ; 16-byte Folded Spill
	stp	x22, x21, [sp, #32]             ; 16-byte Folded Spill
	stp	x20, x19, [sp, #48]             ; 16-byte Folded Spill
	stp	x29, x30, [sp, #64]             ; 16-byte Folded Spill
	add	x29, sp, #64
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	mov	x20, x5
	mov	x19, x4
	add	x21, x0, #8, lsl #12            ; =32768
	ldr	w8, [x0, #8]
	cmp	w8, #500
	b.lt	LBB3_6
; %bb.2:
	ldr	x8, [x21, #24]
	sxtw	x9, w19
	sxtw	x10, w20
	sub	w11, w19, w3
	b	LBB3_4
LBB3_3:                                 ;   in Loop: Header=BB3_4 Depth=1
	add	x9, x9, #1
	add	w11, w11, #1
	cmp	x10, x9
	b.eq	LBB3_23
LBB3_4:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x12, [x8, x9, lsl #3]
	cmp	x12, x2
	b.le	LBB3_3
; %bb.5:                                ;   in Loop: Header=BB3_4 Depth=1
	str	x2, [x8, x9, lsl #3]
	add	w12, w11, #1
	ldr	x13, [x21, #32]
	strh	w12, [x13, x9, lsl #1]
	b	LBB3_3
LBB3_6:
	ldr	x8, [x21, #440]
	cbz	x8, LBB3_8
; %bb.7:
	add	x9, x21, #440
	b	LBB3_10
LBB3_8:
	ldr	x8, [x21, #448]
	cbz	x8, LBB3_25
; %bb.9:
	add	x9, x21, #448
LBB3_10:
	ldr	x10, [x8, #32]
	str	x10, [x9]
LBB3_11:
	str	x2, [x8]
	stp	w20, w3, [x8, #12]
	str	w19, [x8, #8]
	cbnz	x1, LBB3_13
; %bb.12:
	ldr	x1, [x0]
	cbz	x1, LBB3_17
LBB3_13:                                ; =>This Inner Loop Header: Depth=1
	ldr	w9, [x1, #8]
	cmp	w9, w19
	b.le	LBB3_17
; %bb.14:                               ;   in Loop: Header=BB3_13 Depth=1
	ldr	x1, [x1, #24]
	cbnz	x1, LBB3_13
	b	LBB3_17
LBB3_15:                                ;   in Loop: Header=BB3_17 Depth=1
	ldr	x1, [x9, #32]
	cbz	x1, LBB3_20
; %bb.16:                               ;   in Loop: Header=BB3_17 Depth=1
	ldr	w10, [x1, #8]
	cmp	w10, w19
	b.ge	LBB3_21
LBB3_17:                                ; =>This Inner Loop Header: Depth=1
	mov	x9, x1
	cbnz	x1, LBB3_15
; %bb.18:
	ldr	x11, [x0]
	str	x11, [x8, #32]
	mov	x10, x0
	cbz	x11, LBB3_22
; %bb.19:
	str	x8, [x11, #24]
	mov	x10, x0
	b	LBB3_22
LBB3_20:
	add	x10, x9, #32
	str	xzr, [x8, #32]
	b	LBB3_22
LBB3_21:
	add	x10, x9, #32
	str	x1, [x8, #32]
	str	x8, [x1, #24]
LBB3_22:
	str	x8, [x10]
	str	x9, [x8, #24]
	ldr	w8, [x0, #8]
	add	w8, w8, #1
	str	w8, [x0, #8]
LBB3_23:
	ldp	x29, x30, [sp, #64]             ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #48]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #32]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #16]             ; 16-byte Folded Reload
	ldp	x26, x25, [sp], #80             ; 16-byte Folded Reload
LBB3_24:
	ret
LBB3_25:
	mov	x22, x0
	mov	w0, #1                          ; =0x1
	mov	x23, x1
	mov	w1, #40                         ; =0x28
	mov	x24, x2
	mov	x25, x3
	bl	_WebPSafeMalloc
	mov	x3, x25
	mov	x1, x23
	mov	x2, x24
	mov	x8, x0
	mov	x0, x22
	cbnz	x8, LBB3_11
; %bb.26:
	ldr	x8, [x21, #24]
	sxtw	x9, w19
                                        ; kill: def $w20 killed $w20 killed $x20 def $x20
	sxtw	x10, w20
	sub	w11, w19, w3
	b	LBB3_28
LBB3_27:                                ;   in Loop: Header=BB3_28 Depth=1
	add	x9, x9, #1
	add	w11, w11, #1
	cmp	x10, x9
	b.eq	LBB3_23
LBB3_28:                                ; =>This Inner Loop Header: Depth=1
	ldr	x12, [x8, x9, lsl #3]
	cmp	x12, x2
	b.le	LBB3_27
; %bb.29:                               ;   in Loop: Header=BB3_28 Depth=1
	str	x2, [x8, x9, lsl #3]
	add	w12, w11, #1
	ldr	x13, [x21, #32]
	strh	w12, [x13, x9, lsl #1]
	b	LBB3_27
	.cfi_endproc
                                        ; -- End function
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; @.memset_pattern
l_.memset_pattern:
	.quad	9223372036854775807             ; 0x7fffffffffffffff
	.quad	9223372036854775807             ; 0x7fffffffffffffff

.subsections_via_symbols
