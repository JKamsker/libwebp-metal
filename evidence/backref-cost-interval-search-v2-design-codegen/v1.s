	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 26, 0	sdk_version 26, 2
	.globl	_VP8LBackwardReferencesTraceBackwards ; -- Begin function VP8LBackwardReferencesTraceBackwards
	.p2align	2
_VP8LBackwardReferencesTraceBackwards:  ; @VP8LBackwardReferencesTraceBackwards
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
	mov	x20, x6
	mov	x25, x5
	str	x4, [sp, #8]                    ; 8-byte Folded Spill
	mov	x28, x3
	mov	x23, x2
	mov	x26, x1
	mov	x27, x0
	mul	w8, w1, w0
	sxtw	x24, w8
	mov	x0, x24
	mov	w1, #2                          ; =0x2
	bl	_WebPSafeMalloc
	mov	x19, x0
	cbz	x0, LBB0_26
; %bb.1:
	bl	_VP8LBackrefCostIntervalSearchV1ExperimentEnabled
	cbz	w0, LBB0_3
; %bb.2:
	bl	_VP8LBackrefCostIntervalSearchV1ExperimentInjectFallback
	cbz	w0, LBB0_4
LBB0_3:
	mov	x0, x27
	mov	x1, x26
	mov	x2, x23
	mov	x3, x28
	ldr	x4, [sp, #8]                    ; 8-byte Folded Reload
	mov	x5, x25
	mov	x6, x19
	mov	w7, #0                          ; =0x0
	bl	_BackwardReferencesHashChainDistanceOnly
	cbnz	w0, LBB0_5
	b	LBB0_26
LBB0_4:
	mov	x0, x27
	mov	x1, x26
	mov	x2, x23
	mov	x3, x28
	ldr	x4, [sp, #8]                    ; 8-byte Folded Reload
	mov	x5, x25
	mov	x6, x19
	mov	w7, #1                          ; =0x1
	bl	_BackwardReferencesHashChainDistanceOnly
	cbz	w0, LBB0_26
LBB0_5:
	add	x8, x19, x24, lsl #1
	sub	x9, x8, #2
	mov	x24, x8
	cmp	x9, x19
	b.lo	LBB0_7
LBB0_6:                                 ; =>This Inner Loop Header: Depth=1
	ldrh	w10, [x9]
	strh	w10, [x24, #-2]!
	sub	x9, x9, x10, lsl #1
	cmp	x9, x19
	b.hs	LBB0_6
LBB0_7:
	sub	x22, x8, x24
	lsr	x21, x22, #1
	cmp	w28, #1
	b.lt	LBB0_28
; %bb.8:
	add	x0, sp, #16
	mov	x1, x28
	bl	_VP8LColorCacheInit
	cbz	w0, LBB0_26
; %bb.9:
	mov	x0, x20
	bl	_VP8LClearBackwardRefs
	cmp	w21, #0
	b.le	LBB0_34
; %bb.10:
	str	w28, [sp, #4]                   ; 4-byte Folded Spill
	mov	x25, #0                         ; =0x0
	mov	w26, #0                         ; =0x0
	mov	w27, #42941                     ; =0xa7bd
	movk	w27, #7733, lsl #16
	ubfx	x28, x22, #1, #31
	b	LBB0_14
LBB0_11:                                ;   in Loop: Header=BB0_14 Depth=1
	str	w9, [x10, w8, sxtw #2]
	ldr	w8, [x23, x22, lsl #2]
	mov	w9, #65536                      ; =0x10000
LBB0_12:                                ;   in Loop: Header=BB0_14 Depth=1
                                        ; kill: def $w8 killed $w8 killed $x8 def $x8
	orr	x1, x9, x8, lsl #32
	mov	x0, x20
	bl	_VP8LBackwardRefsCursorAdd
LBB0_13:                                ;   in Loop: Header=BB0_14 Depth=1
	add	w26, w26, w21
	add	x25, x25, #1
	cmp	x25, x28
	b.eq	LBB0_33
LBB0_14:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB0_21 Depth 2
                                        ;     Child Loop BB0_25 Depth 2
	ldrh	w8, [x24, x25, lsl #1]
	and	w21, w8, #0xffff
	mov	w22, w26
	cmp	w21, #1
	b.ne	LBB0_18
; %bb.15:                               ;   in Loop: Header=BB0_14 Depth=1
	ldr	w9, [x23, w26, uxtw #2]
	ldr	x10, [sp, #16]
	ldr	w8, [sp, #24]
	mul	w11, w9, w27
	lsr	w8, w11, w8
	ldr	w11, [x10, w8, sxtw #2]
	cmp	w11, w9
	b.ne	LBB0_11
; %bb.16:                               ;   in Loop: Header=BB0_14 Depth=1
	tbnz	w8, #31, LBB0_11
; %bb.17:                               ;   in Loop: Header=BB0_14 Depth=1
	mov	w9, #65537                      ; =0x10001
	b	LBB0_12
LBB0_18:                                ;   in Loop: Header=BB0_14 Depth=1
	ldr	x8, [sp, #8]                    ; 8-byte Folded Reload
	ldr	x8, [x8]
	ldr	w8, [x8, w26, uxtw #2]
	lsl	x8, x8, #20
	and	x8, x8, #0xfffff00000000
	orr	x8, x8, x21, lsl #16
	orr	x1, x8, #0x2
	mov	x0, x20
	bl	_VP8LBackwardRefsCursorAdd
	cbz	w21, LBB0_13
; %bb.19:                               ;   in Loop: Header=BB0_14 Depth=1
	mov	x11, #0                         ; =0x0
	ldr	x8, [sp, #16]
	sub	x9, x21, #1
	mov	x10, #-6148914691236517206      ; =0xaaaaaaaaaaaaaaaa
	movk	x10, #43691
	umulh	x10, x9, x10
	lsr	x10, x10, #2
	mov	w12, #6                         ; =0x6
	msub	x9, x10, x12, x9
	add	x10, x9, #1
	cmp	x10, #6
	csinc	x9, xzr, x9, eq
	cmp	w21, #6
	b.lo	LBB0_23
; %bb.20:                               ;   in Loop: Header=BB0_14 Depth=1
	mov	x11, #0                         ; =0x0
	add	x12, x23, x22, lsl #2
	add	x12, x12, #12
	sub	x13, x9, x21
LBB0_21:                                ;   Parent Loop BB0_14 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldur	w14, [x12, #-12]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldur	w14, [x12, #-8]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldur	w14, [x12, #-4]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12, #4]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	ldr	w14, [x12, #8]
	ldr	w15, [sp, #24]
	mul	w16, w14, w27
	lsr	w15, w16, w15
	str	w14, [x8, w15, sxtw #2]
	sub	x11, x11, #6
	add	x12, x12, #24
	cmp	x13, x11
	b.ne	LBB0_21
; %bb.22:                               ;   in Loop: Header=BB0_14 Depth=1
	neg	x11, x11
LBB0_23:                                ;   in Loop: Header=BB0_14 Depth=1
	cmp	x10, #6
	b.eq	LBB0_13
; %bb.24:                               ;   in Loop: Header=BB0_14 Depth=1
	lsl	x10, x11, #2
	add	x10, x10, x22, lsl #2
	add	x10, x23, x10
LBB0_25:                                ;   Parent Loop BB0_14 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	w11, [x10], #4
	ldr	w12, [sp, #24]
	mul	w13, w11, w27
	lsr	w12, w13, w12
	str	w11, [x8, w12, sxtw #2]
	subs	x9, x9, #1
	b.ne	LBB0_25
	b	LBB0_13
LBB0_26:
	mov	w20, #0                         ; =0x0
LBB0_27:
	mov	x0, x19
	bl	_WebPSafeFree
	mov	x0, x20
	ldp	x29, x30, [sp, #112]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #96]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #80]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #64]             ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #48]             ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #32]             ; 16-byte Folded Reload
	add	sp, sp, #128
	ret
LBB0_28:
	mov	x0, x20
	bl	_VP8LClearBackwardRefs
	cmp	w21, #0
	b.le	LBB0_36
; %bb.29:
	str	w28, [sp, #4]                   ; 4-byte Folded Spill
	mov	w21, #0                         ; =0x0
	ubfx	x22, x22, #1, #31
	mov	w25, #65536                     ; =0x10000
	b	LBB0_31
LBB0_30:                                ;   in Loop: Header=BB0_31 Depth=1
	ldr	w8, [x23, w21, uxtw #2]
	orr	x1, x25, x8, lsl #32
	mov	x0, x20
	bl	_VP8LBackwardRefsCursorAdd
	add	w21, w21, w26
	subs	x22, x22, #1
	b.eq	LBB0_33
LBB0_31:                                ; =>This Inner Loop Header: Depth=1
	ldrh	w26, [x24], #2
	cmp	w26, #1
	b.eq	LBB0_30
; %bb.32:                               ;   in Loop: Header=BB0_31 Depth=1
	ldr	x8, [sp, #8]                    ; 8-byte Folded Reload
	ldr	x8, [x8]
	ldr	w8, [x8, w21, uxtw #2]
	lsl	x8, x8, #20
	and	x8, x8, #0xfffff00000000
	orr	x8, x8, x26, lsl #16
	orr	x1, x8, #0x2
	mov	x0, x20
	bl	_VP8LBackwardRefsCursorAdd
	add	w21, w21, w26
	subs	x22, x22, #1
	b.ne	LBB0_31
LBB0_33:
	ldr	w8, [x20, #4]
	cmp	w8, #0
	cset	w20, eq
	ldr	w8, [sp, #4]                    ; 4-byte Folded Reload
	cmp	w8, #1
	b.ge	LBB0_35
	b	LBB0_27
LBB0_34:
	ldr	w8, [x20, #4]
	cmp	w8, #0
	cset	w20, eq
LBB0_35:
	add	x0, sp, #16
	bl	_VP8LColorCacheClear
	b	LBB0_27
LBB0_36:
	ldr	w8, [x20, #4]
	cmp	w8, #0
	cset	w20, eq
	b	LBB0_27
	.cfi_endproc
                                        ; -- End function
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; -- Begin function BackwardReferencesHashChainDistanceOnly
lCPI1_0:
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
lCPI1_1:
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
lCPI1_2:
	.long	0                               ; 0x0
	.long	1                               ; 0x1
	.section	__TEXT,__text,regular,pure_instructions
	.p2align	2
_BackwardReferencesHashChainDistanceOnly: ; @BackwardReferencesHashChainDistanceOnly
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
	mov	x22, x7
	mov	x28, x6
	mov	x21, x5
	stp	x2, x4, [sp, #64]               ; 16-byte Folded Spill
	mov	x25, x3
	mov	x27, x1
	mov	x23, x0
	mov	w8, #1                          ; =0x1
	lsl	w8, w8, w3
	add	w8, w8, #280
	mov	w9, #280                        ; =0x118
	cmp	w3, #1
	csel	w8, w9, w8, lt
	sbfiz	x8, x8, #2, #32
	add	x1, x8, #3240
	mov	w0, #1                          ; =0x1
	bl	_WebPSafeCalloc
	mov	x24, x0
	mov	w0, #1                          ; =0x1
	mov	w1, #33232                      ; =0x81d0
	bl	_WebPSafeCalloc
	mov	x20, x0
	cmp	x24, #0
	ccmp	x0, #0, #4, ne
	b.ne	LBB1_2
LBB1_1:
	mov	w22, #0                         ; =0x0
	b	LBB1_190
LBB1_2:
	add	x8, x24, #3240
	str	x8, [x24, #3232]
	cmp	w25, #1
	b.lt	LBB1_4
; %bb.3:
	sub	x0, x29, #96
	mov	x1, x25
	bl	_VP8LColorCacheInit
	cbz	w0, LBB1_1
LBB1_4:
	mov	x0, x25
	bl	_VP8LAllocateHistogram
	cbz	x0, LBB1_21
; %bb.5:
	mov	x26, x0
	mov	w19, #1                         ; =0x1
	mov	x1, x25
	mov	w2, #1                          ; =0x1
	bl	_VP8LHistogramInit
Lloh0:
	adrp	x1, _VP8LDistanceToPlaneCode@GOTPAGE
Lloh1:
	ldr	x1, [x1, _VP8LDistanceToPlaneCode@GOTPAGEOFF]
	str	x21, [sp]                       ; 8-byte Folded Spill
	mov	x0, x21
	str	w23, [sp, #28]                  ; 4-byte Folded Spill
	mov	x2, x23
	mov	x3, x26
	bl	_VP8LHistogramStoreRefs
	ldr	w8, [x26, #3240]
	lsl	w9, w19, w8
	add	w9, w9, #280
	mov	w10, #280                       ; =0x118
	cmp	w8, #0
	csel	w19, w9, w10, gt
	ldr	x23, [x24, #3232]
	cmp	w19, #1
	str	x24, [sp, #112]                 ; 8-byte Folded Spill
	str	w25, [sp, #84]                  ; 4-byte Folded Spill
	str	x28, [sp, #48]                  ; 8-byte Folded Spill
	b.lt	LBB1_16
; %bb.6:
	ldr	x21, [x26]
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	and	x9, x19, #0x7ffffff0
	mov	x8, x9
	add	x10, x21, #32
	mov	x11, x9
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
LBB1_7:                                 ; =>This Inner Loop Header: Depth=1
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
	b.ne	LBB1_7
; %bb.8:
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
	b.eq	LBB1_15
; %bb.9:
	tst	x19, #0xc
	b.eq	LBB1_13
; %bb.10:
	and	x8, x19, #0x7ffffffc
	movi.2d	v1, #0000000000000000
	mov.s	v1[0], v0[0]
	movi.2d	v0, #0000000000000000
	mov.s	v0[0], v2[0]
	ubfx	x10, x19, #4, #27
	add	x10, x21, x10, lsl #6
	sub	x9, x8, x9
LBB1_11:                                ; =>This Inner Loop Header: Depth=1
	ldr	q2, [x10], #16
	add.4s	v1, v2, v1
	cmtst.4s	v2, v2, v2
	sub.4s	v0, v0, v2
	subs	x9, x9, #4
	b.ne	LBB1_11
; %bb.12:
	addv.4s	s1, v1
	fmov	w0, s1
	addv.4s	s0, v0
	fmov	w10, s0
	cmp	x8, x19
	b.eq	LBB1_15
LBB1_13:
	sub	x9, x19, x8
	add	x8, x21, x8, lsl #2
LBB1_14:                                ; =>This Inner Loop Header: Depth=1
	ldr	w11, [x8], #4
	add	w0, w11, w0
	cmp	w11, #0
	cinc	w10, w10, ne
	subs	x9, x9, #1
	b.ne	LBB1_14
LBB1_15:
	cmp	w10, #1
	b.hi	LBB1_24
LBB1_16:
	sbfiz	x1, x19, #2, #32
	mov	x0, x23
	bl	_bzero
LBB1_17:
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	ldr	w9, [sp, #28]                   ; 4-byte Folded Reload
	mul	w10, w27, w9
	add	x25, x20, #8, lsl #12           ; =32768
	add	x24, x26, #3080
	add	x19, x26, #8
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB1_18:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x26, x8
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
	b.ne	LBB1_18
; %bb.19:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	ldr	x9, [sp, #112]                  ; 8-byte Folded Reload
	add	x9, x9, #1024
	cmp	w8, #1
	str	x10, [sp, #56]                  ; 8-byte Folded Spill
	str	x9, [sp, #104]                  ; 8-byte Folded Spill
	b.hi	LBB1_22
; %bb.20:
	mov	x0, x9
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB1_31
LBB1_21:
	bl	_VP8LFreeHistogram
	mov	w22, #0                         ; =0x0
	cmp	w25, #1
	b.ge	LBB1_189
	b	LBB1_190
LBB1_22:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
Lloh2:
	adrp	x21, _VP8LFastLog2Slow@GOTPAGE
Lloh3:
	ldr	x21, [x21, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh4:
	adrp	x27, _kLog2Table@GOTPAGE
Lloh5:
	ldr	x27, [x27, _kLog2Table@GOTPAGEOFF]
	cmp	w0, #255
	b.hi	LBB1_26
; %bb.23:
	ldr	w23, [x27, w0, uxtw #2]
	b	LBB1_27
LBB1_24:
	cmp	w0, #255
	b.hi	LBB1_83
; %bb.25:
Lloh6:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh7:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w24, [x8, w0, uxtw #2]
	b	LBB1_84
LBB1_26:
	ldr	x8, [x21]
	blr	x8
	ldr	x9, [sp, #104]                  ; 8-byte Folded Reload
	mov	x23, x0
LBB1_27:
	mov	x28, #0                         ; =0x0
	b	LBB1_29
LBB1_28:                                ;   in Loop: Header=BB1_29 Depth=1
	ldr	x8, [x21]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x9, [sp, #104]                  ; 8-byte Folded Reload
	sub	w8, w23, w0
	str	w8, [x9, x28]
	add	x28, x28, #4
	cmp	x28, #1024
	b.eq	LBB1_31
LBB1_29:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x28]
	cmp	w0, #255
	b.hi	LBB1_28
; %bb.30:                               ;   in Loop: Header=BB1_29 Depth=1
	ldr	w0, [x27, x0, lsl #2]
	sub	w8, w23, w0
	str	w8, [x9, x28]
	add	x28, x28, #4
	cmp	x28, #1024
	b.ne	LBB1_29
LBB1_31:
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	add	x19, x26, #1032
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB1_32:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x26, x8
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
	b.ne	LBB1_32
; %bb.33:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	ldr	x9, [sp, #112]                  ; 8-byte Folded Reload
	add	x9, x9, #2048
	cmp	w8, #1
	str	x9, [sp, #96]                   ; 8-byte Folded Spill
	b.hi	LBB1_35
; %bb.34:
	mov	x0, x9
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB1_42
LBB1_35:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
	cmp	w0, #255
	b.hi	LBB1_37
; %bb.36:
Lloh8:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh9:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w23, [x8, w0, uxtw #2]
	b	LBB1_38
LBB1_37:
Lloh10:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh11:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh12:
	ldr	x8, [x8]
	blr	x8
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	mov	x23, x0
LBB1_38:
	mov	x21, #0                         ; =0x0
Lloh13:
	adrp	x27, _kLog2Table@GOTPAGE
Lloh14:
	ldr	x27, [x27, _kLog2Table@GOTPAGEOFF]
Lloh15:
	adrp	x28, _VP8LFastLog2Slow@GOTPAGE
Lloh16:
	ldr	x28, [x28, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB1_40
LBB1_39:                                ;   in Loop: Header=BB1_40 Depth=1
	ldr	x8, [x28]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x9, [sp, #96]                   ; 8-byte Folded Reload
	sub	w8, w23, w0
	str	w8, [x9, x21]
	add	x21, x21, #4
	cmp	x21, #1024
	b.eq	LBB1_42
LBB1_40:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x21]
	cmp	w0, #255
	b.hi	LBB1_39
; %bb.41:                               ;   in Loop: Header=BB1_40 Depth=1
	ldr	w0, [x27, x0, lsl #2]
	sub	w8, w23, w0
	str	w8, [x9, x21]
	add	x21, x21, #4
	cmp	x21, #1024
	b.ne	LBB1_40
LBB1_42:
	mov	x8, #0                          ; =0x0
	movi.2d	v0, #0000000000000000
	movi.2d	v1, #0000000000000000
	add	x19, x26, #2056
	movi.2d	v2, #0000000000000000
	movi.2d	v3, #0000000000000000
	movi.2d	v4, #0000000000000000
	movi.2d	v5, #0000000000000000
	movi.2d	v6, #0000000000000000
	movi.2d	v7, #0000000000000000
LBB1_43:                                ; =>This Inner Loop Header: Depth=1
	add	x9, x26, x8
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
	b.ne	LBB1_43
; %bb.44:
	add.4s	v4, v5, v4
	add.4s	v5, v7, v6
	add.4s	v4, v5, v4
	addv.4s	s4, v4
	fmov	w8, s4
	cmp	w8, #1
	b.hi	LBB1_46
; %bb.45:
	ldr	x0, [sp, #112]                  ; 8-byte Folded Reload
	mov	w1, #1024                       ; =0x400
	bl	_bzero
	b	LBB1_53
LBB1_46:
	add.4s	v0, v1, v0
	add.4s	v0, v2, v0
	add.4s	v0, v3, v0
	addv.4s	s0, v0
	fmov	w0, s0
	cmp	w0, #255
	b.hi	LBB1_48
; %bb.47:
Lloh17:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh18:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w23, [x8, w0, uxtw #2]
	b	LBB1_49
LBB1_48:
Lloh19:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh20:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh21:
	ldr	x8, [x8]
	blr	x8
	mov	x23, x0
LBB1_49:
	mov	x21, #0                         ; =0x0
Lloh22:
	adrp	x27, _kLog2Table@GOTPAGE
Lloh23:
	ldr	x27, [x27, _kLog2Table@GOTPAGEOFF]
Lloh24:
	adrp	x28, _VP8LFastLog2Slow@GOTPAGE
Lloh25:
	ldr	x28, [x28, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB1_51
LBB1_50:                                ;   in Loop: Header=BB1_51 Depth=1
	ldr	x8, [x28]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	sub	w8, w23, w0
	ldr	x9, [sp, #112]                  ; 8-byte Folded Reload
	str	w8, [x9, x21]
	add	x21, x21, #4
	cmp	x21, #1024
	b.eq	LBB1_53
LBB1_51:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x19, x21]
	cmp	w0, #255
	b.hi	LBB1_50
; %bb.52:                               ;   in Loop: Header=BB1_51 Depth=1
	ldr	w0, [x27, x0, lsl #2]
	sub	w8, w23, w0
	ldr	x9, [sp, #112]                  ; 8-byte Folded Reload
	str	w8, [x9, x21]
	add	x21, x21, #4
	cmp	x21, #1024
	b.ne	LBB1_51
LBB1_53:
	ldp	q7, q6, [x24, #32]
	ldp	q5, q3, [x24, #64]
	ldp	q1, q0, [x24, #96]
	ldp	q17, q16, [x24]
	cmeq.4s	v2, v0, #0
	cmeq.4s	v4, v1, #0
	uzp1.8h	v2, v4, v2
	cmeq.4s	v4, v3, #0
	cmeq.4s	v18, v5, #0
	uzp1.8h	v4, v18, v4
	uzp1.16b	v2, v4, v2
Lloh26:
	adrp	x8, lCPI1_0@PAGE
Lloh27:
	ldr	q4, [x8, lCPI1_0@PAGEOFF]
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
	ldp	q4, q2, [x24, #128]
	cmeq.4s	v18, v2, #0
	cmeq.4s	v19, v4, #0
	uzp1.8h	v18, v19, v18
Lloh28:
	adrp	x8, lCPI1_1@PAGE
Lloh29:
	ldr	q19, [x8, lCPI1_1@PAGEOFF]
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
	ldr	x9, [sp, #112]                  ; 8-byte Folded Reload
	add	x13, x9, #3072
	cmp	w8, #1
	str	x13, [sp, #88]                  ; 8-byte Folded Spill
	b.hi	LBB1_55
; %bb.54:
	movi.2d	v0, #0000000000000000
	stp	q0, q0, [x13, #128]
	stp	q0, q0, [x13, #96]
	stp	q0, q0, [x13, #64]
	stp	q0, q0, [x13, #32]
	stp	q0, q0, [x13]
	ldr	x28, [sp, #48]                  ; 8-byte Folded Reload
	b	LBB1_62
LBB1_55:
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
	ldr	x28, [sp, #48]                  ; 8-byte Folded Reload
	b.hi	LBB1_57
; %bb.56:
Lloh30:
	adrp	x8, _kLog2Table@GOTPAGE
Lloh31:
	ldr	x8, [x8, _kLog2Table@GOTPAGEOFF]
	ldr	w23, [x8, w0, uxtw #2]
	b	LBB1_58
LBB1_57:
Lloh32:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh33:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh34:
	ldr	x8, [x8]
	blr	x8
	ldr	x13, [sp, #88]                  ; 8-byte Folded Reload
	mov	x23, x0
LBB1_58:
	mov	x19, #0                         ; =0x0
Lloh35:
	adrp	x21, _kLog2Table@GOTPAGE
Lloh36:
	ldr	x21, [x21, _kLog2Table@GOTPAGEOFF]
Lloh37:
	adrp	x27, _VP8LFastLog2Slow@GOTPAGE
Lloh38:
	ldr	x27, [x27, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB1_60
LBB1_59:                                ;   in Loop: Header=BB1_60 Depth=1
	ldr	x8, [x27]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	ldr	x13, [sp, #88]                  ; 8-byte Folded Reload
	sub	w8, w23, w0
	str	w8, [x13, x19]
	add	x19, x19, #4
	cmp	x19, #160
	b.eq	LBB1_62
LBB1_60:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x24, x19]
	cmp	w0, #255
	b.hi	LBB1_59
; %bb.61:                               ;   in Loop: Header=BB1_60 Depth=1
	ldr	w0, [x21, x0, lsl #2]
	sub	w8, w23, w0
	str	w8, [x13, x19]
	add	x19, x19, #4
	cmp	x19, #160
	b.ne	LBB1_60
LBB1_62:
	mov	x0, x26
	bl	_VP8LFreeHistogram
	mov	w8, #4095                       ; =0xfff
	str	xzr, [x20, #24]
	ldr	x15, [sp, #56]                  ; 8-byte Folded Reload
	cmp	w15, #4095
	csel	w19, w15, w8, lt
	stp	xzr, xzr, [x20]
	str	xzr, [x25, #456]
	stp	w22, wzr, [x20, #16]
	stp	xzr, x28, [x25, #32]
	mov	w8, #32816                      ; =0x8030
	add	x9, x20, x8
	str	x9, [sp, #40]                   ; 8-byte Folded Spill
	str	xzr, [x25, #80]
	mov	w8, #32856                      ; =0x8058
	add	x8, x20, x8
	str	x9, [x25, #120]
	mov	w9, #32896                      ; =0x8080
	add	x9, x20, x9
	str	x8, [x25, #160]
	mov	w8, #32936                      ; =0x80a8
	add	x8, x20, x8
	str	x9, [x25, #200]
	mov	w9, #32976                      ; =0x80d0
	add	x9, x20, x9
	str	x8, [x25, #240]
	mov	w8, #33016                      ; =0x80f8
	add	x8, x20, x8
	str	x9, [x25, #280]
	mov	w9, #33056                      ; =0x8120
	add	x9, x20, x9
	str	x8, [x25, #320]
	mov	w8, #33096                      ; =0x8148
	add	x8, x20, x8
	str	x9, [x25, #360]
	mov	w9, #33136                      ; =0x8170
	add	x9, x20, x9
	str	x8, [x25, #400]
	mov	w8, #33176                      ; =0x8198
	add	x8, x20, x8
	str	x8, [sp, #32]                   ; 8-byte Folded Spill
	stp	x9, x8, [x25, #440]
	cmp	w15, #0
	b.le	LBB1_71
; %bb.63:
	mov	x9, #0                          ; =0x0
	ldr	x24, [sp, #112]                 ; 8-byte Folded Reload
	ldr	x8, [x24, #3232]
	add	x10, x8, #1024
	add	x8, x20, #40
Lloh39:
	adrp	x11, _kPrefixEncodeCode@GOTPAGE
Lloh40:
	ldr	x11, [x11, _kPrefixEncodeCode@GOTPAGEOFF]
	add	x11, x11, #1
	b	LBB1_66
LBB1_64:                                ;   in Loop: Header=BB1_66 Depth=1
	sub	w13, w9, #1
	clz	w12, w13
	eor	w14, w12, #0x1f
	sub	w12, w14, #1
	lsr	w13, w13, w12
	and	w13, w13, #0x1
	orr	w13, w13, w14, lsl #1
LBB1_65:                                ;   in Loop: Header=BB1_66 Depth=1
	ldr	w13, [x10, w13, sxtw #2]
	sxtw	x12, w12
	add	x12, x13, x12, lsl #23
	str	x12, [x8, x9, lsl #3]
	add	x9, x9, #1
	add	x11, x11, #2
	cmp	x19, x9
	b.eq	LBB1_68
LBB1_66:                                ; =>This Inner Loop Header: Depth=1
	cmp	x9, #511
	b.hi	LBB1_64
; %bb.67:                               ;   in Loop: Header=BB1_66 Depth=1
	ldursb	w13, [x11, #-1]
	ldrsb	w12, [x11]
	b	LBB1_65
LBB1_68:
	mov	w0, #1                          ; =0x1
	str	x0, [x20, #32]
	cmp	w15, #1
	b.ne	LBB1_75
; %bb.69:
	mov	w21, #0                         ; =0x0
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x20, #24]
	cbnz	x0, LBB1_72
LBB1_70:
	mov	x0, x20
	bl	_CostManagerClear
	mov	w22, #0                         ; =0x0
	b	LBB1_188
LBB1_71:
	mov	w21, #0                         ; =0x0
	mov	w0, #1                          ; =0x1
	str	x0, [x20, #32]
	ldr	x24, [sp, #112]                 ; 8-byte Folded Reload
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x20, #24]
	cbz	x0, LBB1_70
LBB1_72:
Lloh41:
	adrp	x8, lCPI1_2@PAGE
Lloh42:
	ldr	d0, [x8, lCPI1_2@PAGEOFF]
	str	d0, [x0, #8]
	mov	x8, x20
	ldr	x13, [x8, #40]!
	str	x13, [x0]
	ldr	x15, [sp, #56]                  ; 8-byte Folded Reload
	cbz	w21, LBB1_126
; %bb.73:
	sub	x11, x19, #1
	sub	x10, x19, #2
	and	x9, x11, #0x7
	cmp	x10, #7
	b.hs	LBB1_88
; %bb.74:
	mov	w10, #1                         ; =0x1
	b	LBB1_125
LBB1_75:
	ldr	x12, [x8]
	sub	x9, x19, #1
	sub	x10, x19, #2
	and	x8, x9, #0x7
	cmp	x10, #7
	b.hs	LBB1_106
; %bb.76:
	mov	w0, #1                          ; =0x1
	mov	w10, #1                         ; =0x1
LBB1_77:
	cbz	x8, LBB1_82
; %bb.78:
	add	x9, x20, x10, lsl #3
	add	x9, x9, #40
	b	LBB1_80
LBB1_79:                                ;   in Loop: Header=BB1_80 Depth=1
	mov	x12, x10
	subs	x8, x8, #1
	b.eq	LBB1_82
LBB1_80:                                ; =>This Inner Loop Header: Depth=1
	ldr	x10, [x9], #8
	cmp	x10, x12
	b.eq	LBB1_79
; %bb.81:                               ;   in Loop: Header=BB1_80 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	b	LBB1_79
LBB1_82:
	mov	w21, #1                         ; =0x1
	mov	w1, #16                         ; =0x10
	bl	_WebPSafeMalloc
	str	x0, [x20, #24]
	cbnz	x0, LBB1_72
	b	LBB1_70
LBB1_83:
Lloh43:
	adrp	x8, _VP8LFastLog2Slow@GOTPAGE
Lloh44:
	ldr	x8, [x8, _VP8LFastLog2Slow@GOTPAGEOFF]
Lloh45:
	ldr	x8, [x8]
	blr	x8
	mov	x24, x0
LBB1_84:
Lloh46:
	adrp	x25, _kLog2Table@GOTPAGE
Lloh47:
	ldr	x25, [x25, _kLog2Table@GOTPAGEOFF]
Lloh48:
	adrp	x28, _VP8LFastLog2Slow@GOTPAGE
Lloh49:
	ldr	x28, [x28, _VP8LFastLog2Slow@GOTPAGEOFF]
	b	LBB1_86
LBB1_85:                                ;   in Loop: Header=BB1_86 Depth=1
	ldr	x8, [x28]
                                        ; kill: def $w0 killed $w0 killed $x0
	blr	x8
	sub	w8, w24, w0
	str	w8, [x23], #4
	subs	x19, x19, #1
	b.eq	LBB1_17
LBB1_86:                                ; =>This Inner Loop Header: Depth=1
	ldr	w0, [x21], #4
	cmp	w0, #255
	b.hi	LBB1_85
; %bb.87:                               ;   in Loop: Header=BB1_86 Depth=1
	ldr	w0, [x25, x0, lsl #2]
	sub	w8, w24, w0
	str	w8, [x23], #4
	subs	x19, x19, #1
	b.ne	LBB1_86
	b	LBB1_17
LBB1_88:
	mov	x10, #0                         ; =0x0
	and	x11, x11, #0xfffffffffffffff8
	add	x12, x20, #56
	b	LBB1_90
LBB1_89:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w14, w10, #9
	str	w14, [x0, #12]
	add	x10, x10, #8
	add	x12, x12, #64
	cmp	x11, x10
	b.eq	LBB1_124
LBB1_90:                                ; =>This Inner Loop Header: Depth=1
	ldur	x14, [x12, #-8]
	cmp	x14, x13
	b.ne	LBB1_98
; %bb.91:                               ;   in Loop: Header=BB1_90 Depth=1
	add	w13, w10, #2
	str	w13, [x0, #12]
	ldr	x13, [x12]
	cmp	x13, x14
	b.ne	LBB1_99
LBB1_92:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w14, w10, #3
	str	w14, [x0, #12]
	ldr	x14, [x12, #8]
	cmp	x14, x13
	b.ne	LBB1_100
LBB1_93:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w13, w10, #4
	str	w13, [x0, #12]
	ldr	x13, [x12, #16]
	cmp	x13, x14
	b.ne	LBB1_101
LBB1_94:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w14, w10, #5
	str	w14, [x0, #12]
	ldr	x14, [x12, #24]
	cmp	x14, x13
	b.ne	LBB1_102
LBB1_95:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w13, w10, #6
	str	w13, [x0, #12]
	ldr	x13, [x12, #32]
	cmp	x13, x14
	b.ne	LBB1_103
LBB1_96:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w14, w10, #7
	str	w14, [x0, #12]
	ldr	x14, [x12, #40]
	cmp	x14, x13
	b.ne	LBB1_104
LBB1_97:                                ;   in Loop: Header=BB1_90 Depth=1
	add	w13, w10, #8
	str	w13, [x0, #12]
	ldr	x13, [x12, #48]
	cmp	x13, x14
	b.eq	LBB1_89
	b	LBB1_105
LBB1_98:                                ;   in Loop: Header=BB1_90 Depth=1
	str	x14, [x0, #16]!
	add	w13, w10, #1
	str	w13, [x0, #8]
	add	w13, w10, #2
	str	w13, [x0, #12]
	ldr	x13, [x12]
	cmp	x13, x14
	b.eq	LBB1_92
LBB1_99:                                ;   in Loop: Header=BB1_90 Depth=1
	str	x13, [x0, #16]!
	add	w14, w10, #2
	str	w14, [x0, #8]
	add	w14, w10, #3
	str	w14, [x0, #12]
	ldr	x14, [x12, #8]
	cmp	x14, x13
	b.eq	LBB1_93
LBB1_100:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x14, [x0, #16]!
	add	w13, w10, #3
	str	w13, [x0, #8]
	add	w13, w10, #4
	str	w13, [x0, #12]
	ldr	x13, [x12, #16]
	cmp	x13, x14
	b.eq	LBB1_94
LBB1_101:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x13, [x0, #16]!
	add	w14, w10, #4
	str	w14, [x0, #8]
	add	w14, w10, #5
	str	w14, [x0, #12]
	ldr	x14, [x12, #24]
	cmp	x14, x13
	b.eq	LBB1_95
LBB1_102:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x14, [x0, #16]!
	add	w13, w10, #5
	str	w13, [x0, #8]
	add	w13, w10, #6
	str	w13, [x0, #12]
	ldr	x13, [x12, #32]
	cmp	x13, x14
	b.eq	LBB1_96
LBB1_103:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x13, [x0, #16]!
	add	w14, w10, #6
	str	w14, [x0, #8]
	add	w14, w10, #7
	str	w14, [x0, #12]
	ldr	x14, [x12, #40]
	cmp	x14, x13
	b.eq	LBB1_97
LBB1_104:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x14, [x0, #16]!
	add	w13, w10, #7
	str	w13, [x0, #8]
	add	w13, w10, #8
	str	w13, [x0, #12]
	ldr	x13, [x12, #48]
	cmp	x13, x14
	b.eq	LBB1_89
LBB1_105:                               ;   in Loop: Header=BB1_90 Depth=1
	str	x13, [x0, #16]!
	add	w14, w10, #8
	str	w14, [x0, #8]
	b	LBB1_89
LBB1_106:
	and	x9, x9, #0xfffffffffffffff8
	add	x11, x20, #56
	mov	w0, #1                          ; =0x1
	mov	w10, #1                         ; =0x1
	b	LBB1_108
LBB1_107:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x10, x10, #8
	add	x11, x11, #64
	subs	x9, x9, #8
	b.eq	LBB1_77
LBB1_108:                               ; =>This Inner Loop Header: Depth=1
	ldur	x13, [x11, #-8]
	cmp	x13, x12
	b.ne	LBB1_116
; %bb.109:                              ;   in Loop: Header=BB1_108 Depth=1
	ldr	x12, [x11]
	cmp	x12, x13
	b.ne	LBB1_117
LBB1_110:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x13, [x11, #8]
	cmp	x13, x12
	b.ne	LBB1_118
LBB1_111:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x12, [x11, #16]
	cmp	x12, x13
	b.ne	LBB1_119
LBB1_112:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x13, [x11, #24]
	cmp	x13, x12
	b.ne	LBB1_120
LBB1_113:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x12, [x11, #32]
	cmp	x12, x13
	b.ne	LBB1_121
LBB1_114:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x13, [x11, #40]
	cmp	x13, x12
	b.ne	LBB1_122
LBB1_115:                               ;   in Loop: Header=BB1_108 Depth=1
	ldr	x12, [x11, #48]
	cmp	x12, x13
	b.eq	LBB1_107
	b	LBB1_123
LBB1_116:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x12, [x11]
	cmp	x12, x13
	b.eq	LBB1_110
LBB1_117:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x13, [x11, #8]
	cmp	x13, x12
	b.eq	LBB1_111
LBB1_118:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x12, [x11, #16]
	cmp	x12, x13
	b.eq	LBB1_112
LBB1_119:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x13, [x11, #24]
	cmp	x13, x12
	b.eq	LBB1_113
LBB1_120:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x12, [x11, #32]
	cmp	x12, x13
	b.eq	LBB1_114
LBB1_121:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x13, [x11, #40]
	cmp	x13, x12
	b.eq	LBB1_115
LBB1_122:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	ldr	x12, [x11, #48]
	cmp	x12, x13
	b.eq	LBB1_107
LBB1_123:                               ;   in Loop: Header=BB1_108 Depth=1
	add	x0, x0, #1
	str	x0, [x20, #32]
	b	LBB1_107
LBB1_124:
	add	x10, x10, #1
LBB1_125:
	cbnz	x9, LBB1_134
LBB1_126:
	sxtw	x0, w15
	mov	w1, #8                          ; =0x8
	mov	x19, x15
	bl	_WebPSafeMalloc
	mov	x22, x0
	str	x0, [x25, #32]
	cbz	x0, LBB1_136
; %bb.127:
	cmp	w19, #1
	mov	x4, x19
	b.lt	LBB1_129
; %bb.128:
	ubfiz	x2, x4, #3, #32
Lloh50:
	adrp	x1, l_.memset_pattern@PAGE
Lloh51:
	add	x1, x1, l_.memset_pattern@PAGEOFF
	mov	x0, x22
	bl	_memset_pattern16
	ldr	x4, [sp, #56]                   ; 8-byte Folded Reload
LBB1_129:
	strh	wzr, [x28]
	ldp	x3, x2, [sp, #64]               ; 16-byte Folded Reload
	ldr	w8, [x3]
	ldr	w9, [sp, #84]                   ; 4-byte Folded Reload
	cmp	w9, #1
	ldp	x6, x5, [sp, #96]               ; 16-byte Folded Reload
	ldp	x30, x7, [sp, #32]              ; 16-byte Folded Reload
	b.lt	LBB1_138
; %bb.130:
	ldur	w10, [x29, #-88]
	ldur	x9, [x29, #-96]
	mov	w11, #42941                     ; =0xa7bd
	movk	w11, #7733, lsl #16
	mul	w11, w8, w11
	lsr	w11, w11, w10
	sxtw	x10, w11
	tbnz	w11, #31, LBB1_137
; %bb.131:
	ldr	w11, [x9, w11, sxtw #2]
	cmp	w11, w8
	b.ne	LBB1_137
; %bb.132:
	ldr	x8, [x24, #3232]
	add	w9, w10, #280
	ldr	w8, [x8, w9, sxtw #2]
	add	x8, x8, x8, lsl #4
	lsl	x8, x8, #2
	b	LBB1_139
LBB1_133:                               ;   in Loop: Header=BB1_134 Depth=1
	add	x10, x10, #1
	str	w10, [x0, #12]
	subs	x9, x9, #1
	b.eq	LBB1_126
LBB1_134:                               ; =>This Inner Loop Header: Depth=1
	mov	x11, x13
	ldr	x13, [x8, x10, lsl #3]
	cmp	x13, x11
	b.eq	LBB1_133
; %bb.135:                              ;   in Loop: Header=BB1_134 Depth=1
	str	x13, [x0, #16]!
	str	w10, [x0, #8]
	b	LBB1_133
LBB1_136:
	mov	x0, x20
	bl	_CostManagerClear
	b	LBB1_188
LBB1_137:
	str	w8, [x9, x10, lsl #2]
LBB1_138:
	lsr	x9, x8, #22
	and	x9, x9, #0x3fc
	ldr	w9, [x24, x9]
	ubfx	x10, x8, #16, #8
	ldr	w10, [x5, x10, lsl #2]
	ldr	x11, [x24, #3232]
	ubfx	x12, x8, #8, #8
	ldr	w11, [x11, x12, lsl #2]
	add	x10, x10, x11
	add	x9, x10, x9
	and	x8, x8, #0xff
	ldr	w8, [x6, x8, lsl #2]
	add	x8, x9, x8
	mov	w9, #82                         ; =0x52
	mul	x8, x8, x9
LBB1_139:
	add	x8, x8, #50
	mov	x9, #36701                      ; =0x8f5d
	movk	x9, #62914, lsl #16
	movk	x9, #23592, lsl #32
	movk	x9, #655, lsl #48
	umulh	x8, x8, x9
	ldr	x9, [x22]
	cmp	x9, x8
	b.le	LBB1_141
; %bb.140:
	str	x8, [x22]
	mov	w8, #1                          ; =0x1
	strh	w8, [x28]
LBB1_141:
	cmp	w4, #2
	b.lt	LBB1_187
; %bb.142:
	add	x21, x20, #8
	mov	x8, #-1                         ; =0xffffffffffffffff
	stp	x8, xzr, [sp, #8]               ; 16-byte Folded Spill
	mov	w9, #-1                         ; =0xffffffff
	mov	w24, #8                         ; =0x8
	mov	w19, #33216                     ; =0x81c0
	mov	w27, #33224                     ; =0x81c8
	mov	w22, #1                         ; =0x1
	mov	w26, #-1                        ; =0xffffffff
	mov	w23, #-1                        ; =0xffffffff
	b	LBB1_144
LBB1_143:                               ;   in Loop: Header=BB1_144 Depth=1
	add	x22, x22, #1
	add	x24, x24, #4
	cmp	x22, x4
	b.eq	LBB1_187
LBB1_144:                               ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_164 Depth 2
                                        ;     Child Loop BB1_171 Depth 2
                                        ;     Child Loop BB1_176 Depth 2
                                        ;     Child Loop BB1_183 Depth 2
	mov	x10, x23
	mov	x12, x26
	ldr	x8, [x25, #32]
	sub	x13, x22, #1
	ldr	x28, [x8, x13, lsl #3]
	ldr	x11, [x2]
	ldr	w14, [x11, x22, lsl #2]
	ldr	w15, [x3, x22, lsl #2]
	ldr	w16, [sp, #84]                  ; 4-byte Folded Reload
	cmp	w16, #1
	b.lt	LBB1_149
; %bb.145:                              ;   in Loop: Header=BB1_144 Depth=1
	ldur	w17, [x29, #-88]
	ldur	x16, [x29, #-96]
	mov	w0, #42941                      ; =0xa7bd
	movk	w0, #7733, lsl #16
	mul	w0, w15, w0
	lsr	w0, w0, w17
	sxtw	x17, w0
	tbnz	w0, #31, LBB1_148
; %bb.146:                              ;   in Loop: Header=BB1_144 Depth=1
	ldr	w0, [x16, w0, sxtw #2]
	cmp	w0, w15
	b.ne	LBB1_148
; %bb.147:                              ;   in Loop: Header=BB1_144 Depth=1
	ldr	x15, [sp, #112]                 ; 8-byte Folded Reload
	ldr	x15, [x15, #3232]
	add	w16, w17, #280
	ldr	w15, [x15, w16, sxtw #2]
	add	x15, x15, x15, lsl #4
	lsl	x15, x15, #2
	b	LBB1_150
LBB1_148:                               ;   in Loop: Header=BB1_144 Depth=1
	str	w15, [x16, x17, lsl #2]
LBB1_149:                               ;   in Loop: Header=BB1_144 Depth=1
	lsr	x16, x15, #22
	and	x16, x16, #0x3fc
	ldr	x0, [sp, #112]                  ; 8-byte Folded Reload
	ldr	w16, [x0, x16]
	ubfx	x17, x15, #16, #8
	ldr	w17, [x5, x17, lsl #2]
	ldr	x0, [x0, #3232]
	ubfx	x1, x15, #8, #8
	ldr	w0, [x0, x1, lsl #2]
	add	x17, x17, x0
	add	x16, x17, x16
	and	x15, x15, #0xff
	ldr	w15, [x6, x15, lsl #2]
	add	x15, x16, x15
	mov	w16, #82                        ; =0x52
	mul	x15, x15, x16
LBB1_150:                               ;   in Loop: Header=BB1_144 Depth=1
	add	x15, x15, #50
	mov	x16, #36701                     ; =0x8f5d
	movk	x16, #62914, lsl #16
	movk	x16, #23592, lsl #32
	movk	x16, #655, lsl #48
	umulh	x15, x15, x16
	ldr	x16, [x8, x22, lsl #3]
	add	x15, x15, x28
	cmp	x16, x15
	b.le	LBB1_153
; %bb.151:                              ;   in Loop: Header=BB1_144 Depth=1
	str	x15, [x8, x22, lsl #3]
	ldr	x15, [sp, #48]                  ; 8-byte Folded Reload
	mov	w16, #1                         ; =0x1
	strh	w16, [x15, x22, lsl #1]
	lsr	w23, w14, #12
	and	w26, w14, #0xfff
	cmp	w26, #2
	b.hs	LBB1_154
LBB1_152:                               ;   in Loop: Header=BB1_144 Depth=1
	ldr	x8, [x20]
	cbnz	x8, LBB1_183
	b	LBB1_143
LBB1_153:                               ;   in Loop: Header=BB1_144 Depth=1
	lsr	w23, w14, #12
	and	w26, w14, #0xfff
	cmp	w26, #2
	b.lo	LBB1_152
LBB1_154:                               ;   in Loop: Header=BB1_144 Depth=1
	cmp	w23, w10
	b.ne	LBB1_158
; %bb.155:                              ;   in Loop: Header=BB1_144 Depth=1
	add	w12, w12, w13
	sub	w12, w12, #1
	cmp	w9, #0
	ldr	x9, [sp, #16]                   ; 8-byte Folded Reload
	csel	w9, w9, w12, eq
	mov	x12, x9
	add	w9, w22, w26
	sub	w9, w9, #1
	cmp	w9, w12
	b.le	LBB1_160
; %bb.156:                              ;   in Loop: Header=BB1_144 Depth=1
	sxtw	x9, w12
	cmp	x22, x9
	b.le	LBB1_163
; %bb.157:                              ;   in Loop: Header=BB1_144 Depth=1
	mov	w19, #0                         ; =0x0
	mov	x2, x22
	b	LBB1_168
LBB1_158:                               ;   in Loop: Header=BB1_144 Depth=1
	ldr	w0, [sp, #28]                   ; 4-byte Folded Reload
	mov	x1, x23
	bl	_VP8LDistanceToPlaneCode
	cmp	w0, #511
	b.gt	LBB1_161
; %bb.159:                              ;   in Loop: Header=BB1_144 Depth=1
Lloh52:
	adrp	x8, _kPrefixEncodeCode@GOTPAGE
Lloh53:
	ldr	x8, [x8, _kPrefixEncodeCode@GOTPAGEOFF]
	add	x8, x8, w0, sxtw #1
	ldrsb	w9, [x8]
	ldrsb	w8, [x8, #1]
	b	LBB1_162
LBB1_160:                               ;   in Loop: Header=BB1_144 Depth=1
	str	x12, [sp, #16]                  ; 8-byte Folded Spill
	mov	w9, #0                          ; =0x0
	ldr	x8, [x20]
	cbnz	x8, LBB1_183
	b	LBB1_143
LBB1_161:                               ;   in Loop: Header=BB1_144 Depth=1
	sub	w9, w0, #1
	clz	w8, w9
	eor	w10, w8, #0x1f
	sub	w8, w10, #1
	lsr	w9, w9, w8
	and	w9, w9, #0x1
	orr	w9, w9, w10, lsl #1
LBB1_162:                               ;   in Loop: Header=BB1_144 Depth=1
	ldr	x10, [sp, #88]                  ; 8-byte Folded Reload
	ldr	w9, [x10, w9, sxtw #2]
	sxtw	x8, w8
	add	x8, x9, x8, lsl #23
	str	x8, [sp, #8]                    ; 8-byte Folded Spill
	add	x1, x8, x28
	mov	x0, x20
	mov	x2, x22
	mov	x3, x26
	bl	_PushInterval
	mov	w9, #1                          ; =0x1
	ldp	x3, x2, [sp, #64]               ; 16-byte Folded Reload
	ldr	x4, [sp, #56]                   ; 8-byte Folded Reload
	ldp	x6, x5, [sp, #96]               ; 16-byte Folded Reload
	ldp	x30, x7, [sp, #32]              ; 16-byte Folded Reload
	ldr	x8, [x20]
	cbnz	x8, LBB1_183
	b	LBB1_143
LBB1_163:                               ;   in Loop: Header=BB1_144 Depth=1
	add	w2, w12, #1
	add	x13, x11, x24
	mov	x12, x22
LBB1_164:                               ;   Parent Loop BB1_144 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	w14, [x13], #4
	cmp	w10, w14, lsr #12
	b.ne	LBB1_167
; %bb.165:                              ;   in Loop: Header=BB1_164 Depth=2
	add	x12, x12, #1
	sub	x15, x12, #1
	cmp	x15, x9
	b.lt	LBB1_164
; %bb.166:                              ;   in Loop: Header=BB1_144 Depth=1
	and	w19, w14, #0xfff
	b	LBB1_168
LBB1_167:                               ;   in Loop: Header=BB1_144 Depth=1
	ldr	w9, [x11, w12, uxtw #2]
	and	w19, w9, #0xfff
	mov	x2, x12
LBB1_168:                               ;   in Loop: Header=BB1_144 Depth=1
	sub	w10, w2, #1
	ldr	x9, [x20]
	sxtw	x28, w10
	cbz	x9, LBB1_180
; %bb.169:                              ;   in Loop: Header=BB1_144 Depth=1
	mov	x10, x9
	b	LBB1_171
LBB1_170:                               ;   in Loop: Header=BB1_171 Depth=2
	cbz	x10, LBB1_176
LBB1_171:                               ;   Parent Loop BB1_144 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x11, x10
	ldr	w10, [x10, #8]
	cmp	w10, w2
	b.ge	LBB1_176
; %bb.172:                              ;   in Loop: Header=BB1_171 Depth=2
	ldr	x10, [x11, #32]
	ldr	w12, [x11, #12]
	cmp	w12, w2
	b.lt	LBB1_170
; %bb.173:                              ;   in Loop: Header=BB1_171 Depth=2
	ldr	x12, [x11]
	ldr	x13, [x8, x28, lsl #3]
	cmp	x13, x12
	b.le	LBB1_170
; %bb.174:                              ;   in Loop: Header=BB1_171 Depth=2
	ldr	w11, [x11, #16]
	sub	w11, w28, w11
	str	x12, [x8, x28, lsl #3]
	add	w11, w11, #1
	ldr	x12, [x25, #40]
	strh	w11, [x12, x28, lsl #1]
	b	LBB1_170
LBB1_175:                               ;   in Loop: Header=BB1_176 Depth=2
	cbz	x9, LBB1_180
LBB1_176:                               ;   Parent Loop BB1_144 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x10, x9
	ldr	w9, [x9, #8]
	cmp	w9, w2
	b.gt	LBB1_180
; %bb.177:                              ;   in Loop: Header=BB1_176 Depth=2
	ldr	x9, [x10, #32]
	ldr	w11, [x10, #12]
	cmp	w11, w2
	b.le	LBB1_175
; %bb.178:                              ;   in Loop: Header=BB1_176 Depth=2
	ldr	x11, [x10]
	ldr	x12, [x8, w2, uxtw #3]
	cmp	x12, x11
	b.le	LBB1_175
; %bb.179:                              ;   in Loop: Header=BB1_176 Depth=2
	ldr	w10, [x10, #16]
	sub	w10, w2, w10
	str	x11, [x8, w2, uxtw #3]
	add	w10, w10, #1
	ldr	x11, [x25, #40]
	strh	w10, [x11, w2, uxtw #1]
	b	LBB1_175
LBB1_180:                               ;   in Loop: Header=BB1_144 Depth=1
	ldr	x8, [x8, x28, lsl #3]
	ldr	x9, [sp, #8]                    ; 8-byte Folded Reload
	add	x1, x8, x9
	mov	x0, x20
	mov	x3, x19
	bl	_PushInterval
	mov	w9, #0                          ; =0x0
	add	w8, w28, w19
	str	x8, [sp, #16]                   ; 8-byte Folded Spill
	ldp	x3, x2, [sp, #64]               ; 16-byte Folded Reload
	ldr	x4, [sp, #56]                   ; 8-byte Folded Reload
	ldp	x6, x5, [sp, #96]               ; 16-byte Folded Reload
	ldp	x30, x7, [sp, #32]              ; 16-byte Folded Reload
	mov	w19, #33216                     ; =0x81c0
	ldr	x8, [x20]
	cbnz	x8, LBB1_183
	b	LBB1_143
LBB1_181:                               ;   in Loop: Header=BB1_183 Depth=2
	ldr	x11, [x10, #24]
	add	x12, x11, #32
	cmp	x11, #0
	csel	x12, x20, x12, eq
	str	x8, [x12]
	add	x12, x8, #24
	cmp	x8, #0
	csel	x12, x21, x12, eq
	str	x11, [x12]
	cmp	x30, x10
	ccmp	x7, x10, #2, hs
	csel	x11, x27, x19, hi
	ldr	x12, [x20, x11]
	str	x10, [x20, x11]
	str	x12, [x10, #32]
	ldr	w10, [x20, #20]
	sub	w10, w10, #1
	str	w10, [x20, #20]
LBB1_182:                               ;   in Loop: Header=BB1_183 Depth=2
	cbz	x8, LBB1_143
LBB1_183:                               ;   Parent Loop BB1_144 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x10, x8
	ldrsw	x8, [x8, #8]
	cmp	x22, x8
	b.lt	LBB1_143
; %bb.184:                              ;   in Loop: Header=BB1_183 Depth=2
	ldr	x8, [x10, #32]
	ldrsw	x11, [x10, #12]
	cmp	x22, x11
	b.ge	LBB1_181
; %bb.185:                              ;   in Loop: Header=BB1_183 Depth=2
	ldr	x11, [x10]
	ldr	x12, [x25, #32]
	ldr	x13, [x12, x22, lsl #3]
	cmp	x13, x11
	b.le	LBB1_182
; %bb.186:                              ;   in Loop: Header=BB1_183 Depth=2
	ldr	w10, [x10, #16]
	sub	w10, w22, w10
	str	x11, [x12, x22, lsl #3]
	add	w10, w10, #1
	ldr	x11, [x25, #40]
	strh	w10, [x11, x22, lsl #1]
	b	LBB1_182
LBB1_187:
	ldr	x8, [sp]                        ; 8-byte Folded Reload
	ldr	w8, [x8, #4]
	cmp	w8, #0
	cset	w22, eq
	ldr	x24, [sp, #112]                 ; 8-byte Folded Reload
LBB1_188:
	ldr	w25, [sp, #84]                  ; 4-byte Folded Reload
	cmp	w25, #1
	b.lt	LBB1_190
LBB1_189:
	sub	x0, x29, #96
	bl	_VP8LColorCacheClear
LBB1_190:
	mov	x0, x20
	bl	_CostManagerClear
	mov	x0, x24
	bl	_WebPSafeFree
	mov	x0, x20
	bl	_WebPSafeFree
	mov	x0, x22
	ldp	x29, x30, [sp, #224]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #208]            ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #192]            ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #176]            ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #160]            ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #144]            ; 16-byte Folded Reload
	add	sp, sp, #240
	ret
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
	b.gt	LBB2_6
; %bb.1:
	cmp	w21, #1
	b.lt	LBB2_26
; %bb.2:
	mov	x8, #0                          ; =0x0
	add	x9, x22, #8, lsl #12            ; =32768
	add	w13, w21, w20
	add	x10, x22, #40
	ldr	x11, [x9, #32]
	sxtw	x12, w20
	sxtw	x13, w13
	b	LBB2_4
LBB2_3:                                 ;   in Loop: Header=BB2_4 Depth=1
	add	x12, x12, #1
	add	x8, x8, #1
	cmp	x12, x13
	b.ge	LBB2_26
LBB2_4:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x14, [x10, x8, lsl #3]
	ldr	x15, [x11, x12, lsl #3]
	add	x14, x14, x19
	cmp	x15, x14
	b.le	LBB2_3
; %bb.5:                                ;   in Loop: Header=BB2_4 Depth=1
	str	x14, [x11, x12, lsl #3]
	add	w14, w8, #1
	ldr	x15, [x9, #40]
	strh	w14, [x15, x12, lsl #1]
	b	LBB2_3
LBB2_6:
	ldr	x8, [x22, #32]
	cbz	x8, LBB2_26
; %bb.7:
	mov	x27, #0                         ; =0x0
	ldr	x9, [x22, #24]
	mov	x8, x22
	ldr	x28, [x8], #8
	stp	x8, x9, [sp, #16]               ; 16-byte Folded Spill
	mov	w8, #32816                      ; =0x8030
	add	x8, x22, x8
	str	x8, [sp, #8]                    ; 8-byte Folded Spill
	mov	w8, #33176                      ; =0x8198
	add	x8, x22, x8
	str	x8, [sp]                        ; 8-byte Folded Spill
	b	LBB2_10
LBB2_8:                                 ;   in Loop: Header=BB2_10 Depth=1
	mov	x25, #0                         ; =0x0
LBB2_9:                                 ;   in Loop: Header=BB2_10 Depth=1
	mov	x0, x22
	mov	x1, x25
	mov	x2, x24
	mov	x3, x20
	mov	x4, x26
	mov	x5, x23
	bl	_InsertInterval
	add	x27, x27, #1
	ldr	x8, [x22, #32]
	mov	x28, x25
	cmp	x27, x8
	b.hs	LBB2_26
LBB2_10:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB2_15 Depth 2
	ldr	x8, [sp, #24]                   ; 8-byte Folded Reload
	add	x8, x8, x27, lsl #4
	ldr	w9, [x8, #8]
	cmp	w9, w21
	b.ge	LBB2_26
; %bb.11:                               ;   in Loop: Header=BB2_10 Depth=1
	add	w26, w9, w20
	ldr	w9, [x8, #12]
	cmp	w9, w21
	csel	w9, w9, w21, lt
	add	w23, w9, w20
	ldr	x8, [x8]
	add	x24, x8, x19
	cbz	x28, LBB2_8
; %bb.12:                               ;   in Loop: Header=BB2_10 Depth=1
	mov	x4, x26
	b	LBB2_15
LBB2_13:                                ;   in Loop: Header=BB2_15 Depth=2
	mov	x0, x22
	mov	x1, x25
	mov	x2, x24
	mov	x3, x20
	bl	_InsertInterval
	mov	x4, x26
	cmp	w26, w23
	b.ge	LBB2_9
LBB2_14:                                ;   in Loop: Header=BB2_15 Depth=2
	cbz	x28, LBB2_22
LBB2_15:                                ;   Parent Loop BB2_10 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	mov	x25, x28
	ldr	w5, [x28, #8]
	cmp	w5, w23
	b.ge	LBB2_23
; %bb.16:                               ;   in Loop: Header=BB2_15 Depth=2
	ldr	x28, [x25, #32]
	ldr	w26, [x25, #12]
	cmp	w4, w26
	b.ge	LBB2_14
; %bb.17:                               ;   in Loop: Header=BB2_15 Depth=2
	ldr	x2, [x25]
	cmp	x24, x2
	b.ge	LBB2_13
; %bb.18:                               ;   in Loop: Header=BB2_15 Depth=2
	cmp	w4, w5
	b.le	LBB2_20
; %bb.19:                               ;   in Loop: Header=BB2_15 Depth=2
	str	w4, [x25, #12]
	cmp	w23, w26
	b.ge	LBB2_14
	b	LBB2_24
LBB2_20:                                ;   in Loop: Header=BB2_15 Depth=2
	cmp	w26, w23
	b.gt	LBB2_25
; %bb.21:                               ;   in Loop: Header=BB2_15 Depth=2
	ldr	x8, [x25, #24]
	add	x9, x8, #32
	cmp	x8, #0
	csel	x9, x22, x9, eq
	str	x28, [x9]
	add	x9, x28, #24
	cmp	x28, #0
	ldr	x10, [sp, #16]                  ; 8-byte Folded Reload
	csel	x9, x10, x9, eq
	str	x8, [x9]
	ldp	x9, x8, [sp]                    ; 16-byte Folded Reload
	cmp	x9, x25
	ccmp	x8, x25, #2, hs
	mov	w8, #33216                      ; =0x81c0
	mov	w9, #33224                      ; =0x81c8
	csel	x8, x9, x8, hi
	ldr	x9, [x22, x8]
	str	x25, [x22, x8]
	str	x9, [x25, #32]
	ldr	w8, [x22, #20]
	sub	w8, w8, #1
	str	w8, [x22, #20]
	b	LBB2_14
LBB2_22:                                ;   in Loop: Header=BB2_10 Depth=1
	mov	x25, #0                         ; =0x0
LBB2_23:                                ;   in Loop: Header=BB2_10 Depth=1
	mov	x26, x4
	b	LBB2_9
LBB2_24:                                ;   in Loop: Header=BB2_10 Depth=1
	ldr	w3, [x25, #16]
	mov	x0, x22
	mov	x1, x25
	mov	x28, x4
	mov	x4, x23
	mov	x5, x26
	bl	_InsertInterval
	ldr	x25, [x25, #32]
	mov	x26, x28
	b	LBB2_9
LBB2_25:                                ;   in Loop: Header=BB2_10 Depth=1
	str	w23, [x25, #8]
	mov	x26, x4
	b	LBB2_9
LBB2_26:
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
lCPI3_0:
	.quad	33136                           ; 0x8170
	.quad	33176                           ; 0x8198
	.section	__TEXT,__text,regular,pure_instructions
	.p2align	2
_CostManagerClear:                      ; @CostManagerClear
	.cfi_startproc
; %bb.0:
	cbz	x0, LBB3_14
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
	ldr	x0, [x20, #32]
	bl	_WebPSafeFree
	ldr	x0, [x19, #24]
	bl	_WebPSafeFree
	ldr	x0, [x19]
	cbz	x0, LBB3_7
; %bb.2:
	mov	w8, #32816                      ; =0x8030
	add	x21, x19, x8
	mov	w8, #33176                      ; =0x8198
	add	x22, x19, x8
	b	LBB3_5
LBB3_3:                                 ;   in Loop: Header=BB3_5 Depth=1
	bl	_WebPSafeFree
LBB3_4:                                 ;   in Loop: Header=BB3_5 Depth=1
	mov	x0, x23
	cbz	x23, LBB3_7
LBB3_5:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x23, [x0, #32]
	cmp	x21, x0
	b.hi	LBB3_3
; %bb.6:                                ;   in Loop: Header=BB3_5 Depth=1
	cmp	x22, x0
	b.hs	LBB3_4
	b	LBB3_3
LBB3_7:
	str	xzr, [x19]
	ldr	x0, [x20, #456]
	cbz	x0, LBB3_13
; %bb.8:
	mov	w8, #32816                      ; =0x8030
	add	x21, x19, x8
	mov	w8, #33176                      ; =0x8198
	add	x22, x19, x8
	b	LBB3_11
LBB3_9:                                 ;   in Loop: Header=BB3_11 Depth=1
	bl	_WebPSafeFree
LBB3_10:                                ;   in Loop: Header=BB3_11 Depth=1
	mov	x0, x23
	cbz	x23, LBB3_13
LBB3_11:                                ; =>This Inner Loop Header: Depth=1
	ldr	x23, [x0, #32]
	cmp	x21, x0
	b.hi	LBB3_9
; %bb.12:                               ;   in Loop: Header=BB3_11 Depth=1
	cmp	x22, x0
	b.hs	LBB3_10
	b	LBB3_9
LBB3_13:
	mov	x0, x19
	mov	w1, #33232                      ; =0x81d0
	bl	_bzero
	mov	w8, #32816                      ; =0x8030
	add	x8, x19, x8
	str	xzr, [x20, #80]
	mov	w9, #32856                      ; =0x8058
	add	x9, x19, x9
	str	x8, [x20, #120]
	mov	w8, #32896                      ; =0x8080
	add	x8, x19, x8
	str	x9, [x20, #160]
	mov	w9, #32936                      ; =0x80a8
	add	x9, x19, x9
	str	x8, [x20, #200]
	mov	w8, #32976                      ; =0x80d0
	add	x8, x19, x8
	str	x9, [x20, #240]
	mov	w9, #33016                      ; =0x80f8
	add	x9, x19, x9
	str	x8, [x20, #280]
	mov	w8, #33056                      ; =0x8120
	add	x8, x19, x8
	str	x9, [x20, #320]
	mov	w9, #33096                      ; =0x8148
	add	x9, x19, x9
	str	x8, [x20, #360]
	dup.2d	v0, x19
Lloh54:
	adrp	x8, lCPI3_0@PAGE
Lloh55:
	ldr	q1, [x8, lCPI3_0@PAGEOFF]
	add.2d	v0, v0, v1
	str	x9, [x20, #400]
	add	x8, x20, #440
	str	q0, [x8]
	ldp	x29, x30, [sp, #48]             ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #32]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #16]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp], #64             ; 16-byte Folded Reload
LBB3_14:
	ret
	.loh AdrpLdr	Lloh54, Lloh55
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function InsertInterval
_InsertInterval:                        ; @InsertInterval
	.cfi_startproc
; %bb.0:
	cmp	w4, w5
	b.ge	LBB4_25
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
	ldr	w8, [x0, #20]
	cmp	w8, #500
	b.lt	LBB4_6
; %bb.2:
	ldr	x8, [x21, #32]
	sxtw	x9, w19
	sxtw	x10, w20
	sub	w11, w19, w3
	b	LBB4_4
LBB4_3:                                 ;   in Loop: Header=BB4_4 Depth=1
	add	x9, x9, #1
	add	w11, w11, #1
	cmp	x10, x9
	b.eq	LBB4_24
LBB4_4:                                 ; =>This Inner Loop Header: Depth=1
	ldr	x12, [x8, x9, lsl #3]
	cmp	x12, x2
	b.le	LBB4_3
; %bb.5:                                ;   in Loop: Header=BB4_4 Depth=1
	str	x2, [x8, x9, lsl #3]
	add	w12, w11, #1
	ldr	x13, [x21, #40]
	strh	w12, [x13, x9, lsl #1]
	b	LBB4_3
LBB4_6:
	ldr	x8, [x21, #448]
	cbz	x8, LBB4_8
; %bb.7:
	add	x9, x21, #448
	b	LBB4_10
LBB4_8:
	ldr	x8, [x21, #456]
	cbz	x8, LBB4_26
; %bb.9:
	add	x9, x21, #456
LBB4_10:
	ldr	x10, [x8, #32]
	str	x10, [x9]
LBB4_11:
	str	x2, [x8]
	stp	w20, w3, [x8, #12]
	str	w19, [x8, #8]
	cbnz	x1, LBB4_16
; %bb.12:
	ldr	w9, [x0, #16]
	cbz	w9, LBB4_15
; %bb.13:
	ldr	x1, [x0, #8]
	cbz	x1, LBB4_15
; %bb.14:
	ldr	w9, [x1, #8]
	cmp	w9, w19
	b.lt	LBB4_16
LBB4_15:
	ldr	x1, [x0]
	cbz	x1, LBB4_20
LBB4_16:                                ; =>This Inner Loop Header: Depth=1
	ldr	w9, [x1, #8]
	cmp	w9, w19
	b.le	LBB4_20
; %bb.17:                               ;   in Loop: Header=BB4_16 Depth=1
	ldr	x1, [x1, #24]
	cbnz	x1, LBB4_16
	b	LBB4_20
LBB4_18:                                ;   in Loop: Header=BB4_20 Depth=1
	ldr	x1, [x9, #32]
	cmp	x1, #0
	cset	w10, eq
	cbz	x1, LBB4_22
; %bb.19:                               ;   in Loop: Header=BB4_20 Depth=1
	ldr	w11, [x1, #8]
	cmp	w11, w19
	b.ge	LBB4_22
LBB4_20:                                ; =>This Inner Loop Header: Depth=1
	mov	x9, x1
	cbnz	x1, LBB4_18
; %bb.21:
	ldr	x1, [x0]
	str	x1, [x8, #32]
	cmp	x1, #0
	cset	w10, eq
	mov	x11, x0
	b	LBB4_23
LBB4_22:
	add	x11, x9, #32
	str	x1, [x8, #32]
LBB4_23:
	add	x12, x1, #24
	add	x13, x0, #8
	cmp	w10, #0
	csel	x10, x13, x12, ne
	str	x8, [x10]
	str	x8, [x11]
	str	x9, [x8, #24]
	ldr	w8, [x0, #20]
	add	w8, w8, #1
	str	w8, [x0, #20]
LBB4_24:
	ldp	x29, x30, [sp, #64]             ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #48]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #32]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #16]             ; 16-byte Folded Reload
	ldp	x26, x25, [sp], #80             ; 16-byte Folded Reload
LBB4_25:
	ret
LBB4_26:
	mov	x22, x0
	mov	w0, #1                          ; =0x1
	mov	x23, x1
	mov	w1, #40                         ; =0x28
	mov	x24, x2
	mov	x25, x3
	bl	_WebPSafeMalloc
	mov	x3, x25
	mov	x2, x24
	mov	x1, x23
	mov	x8, x0
	mov	x0, x22
	cbnz	x8, LBB4_11
; %bb.27:
	ldr	x8, [x21, #32]
	sxtw	x9, w19
                                        ; kill: def $w20 killed $w20 killed $x20 def $x20
	sxtw	x10, w20
	sub	w11, w19, w3
	b	LBB4_29
LBB4_28:                                ;   in Loop: Header=BB4_29 Depth=1
	add	x9, x9, #1
	add	w11, w11, #1
	cmp	x10, x9
	b.eq	LBB4_24
LBB4_29:                                ; =>This Inner Loop Header: Depth=1
	ldr	x12, [x8, x9, lsl #3]
	cmp	x12, x2
	b.le	LBB4_28
; %bb.30:                               ;   in Loop: Header=BB4_29 Depth=1
	str	x2, [x8, x9, lsl #3]
	add	w12, w11, #1
	ldr	x13, [x21, #40]
	strh	w12, [x13, x9, lsl #1]
	b	LBB4_28
	.cfi_endproc
                                        ; -- End function
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; @.memset_pattern
l_.memset_pattern:
	.quad	9223372036854775807             ; 0x7fffffffffffffff
	.quad	9223372036854775807             ; 0x7fffffffffffffff

.subsections_via_symbols
