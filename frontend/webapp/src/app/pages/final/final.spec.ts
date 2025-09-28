import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Final } from './final';

describe('Final', () => {
  let component: Final;
  let fixture: ComponentFixture<Final>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Final]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Final);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
