package com.orez.usb;
import org.junit.Test;
import static org.junit.Assert.*;
public class HybridIsoValidatorTest {
 @Test public void acceptsHybridMbrPartition() {
  byte[] mbr=new byte[512]; mbr[450]=0x17; mbr[458]=1; mbr[510]=0x55; mbr[511]=(byte)0xaa;
  assertTrue(HybridIsoValidator.hasMbrPartition(mbr));
 }
 @Test public void rejectsPlainMbrWithoutPartition() {
  byte[] mbr=new byte[512]; mbr[510]=0x55; mbr[511]=(byte)0xaa;
  assertFalse(HybridIsoValidator.hasMbrPartition(mbr));
 }
 @Test public void validatesElToritoCatalogChecksum() {
  byte[] c=new byte[64]; c[0]=1; c[30]=0x55; c[31]=(byte)0xaa; c[32]=(byte)0x88;
  int sum=0; for(int i=0;i<32;i+=2) sum=(sum+(c[i]&255)+((c[i+1]&255)<<8))&0xffff;
  int neg=(-sum)&0xffff; c[28]=(byte)neg; c[29]=(byte)(neg>>>8);
  assertTrue(HybridIsoValidator.validBootCatalog(c)); c[7]^=1;
  assertFalse(HybridIsoValidator.validBootCatalog(c));
 }
}